#!/usr/bin/env python3

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import open_cloud_request


class MultipartBodyTests(unittest.TestCase):
    def test_text_and_repeated_file_fields_build_valid_multipart_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory, "first.png")
            second = Path(directory, "second.jpg")
            first.write_bytes(b"first-image")
            second.write_bytes(b"second-image")

            with mock.patch.object(open_cloud_request.secrets, "token_hex", return_value="fixed"):
                body, content_type = open_cloud_request.build_multipart_body(
                    [f"files={first}", f"files={second}"],
                    ["name=Example asset", "description=テスト=値"],
                )

        self.assertEqual(
            content_type,
            "multipart/form-data; boundary=roblox-open-cloud-fixed",
        )
        self.assertEqual(body.count(b'name="files"'), 2)
        self.assertIn(b'name="name"\r\n\r\nExample asset', body)
        self.assertIn('name="description"\r\n\r\nテスト=値'.encode(), body)
        self.assertIn(b'filename="first.png"', body)
        self.assertIn(b'filename="second.jpg"', body)
        self.assertIn(b"Content-Type: image/png", body)
        self.assertIn(b"Content-Type: image/jpeg", body)
        self.assertIn(b"first-image", body)
        self.assertIn(b"second-image", body)
        self.assertTrue(body.endswith(b"--roblox-open-cloud-fixed--\r\n"))

    def test_data_file_and_multipart_file_are_mutually_exclusive(self) -> None:
        args = argparse.Namespace(
            data_file="request.json",
            multipart_file=["files=thumbnail.png"],
            multipart_field=[],
            content_type=None,
        )

        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            open_cloud_request.read_request_body(args)

    def test_data_file_and_multipart_field_are_mutually_exclusive(self) -> None:
        args = argparse.Namespace(
            data_file="request.json",
            multipart_file=[],
            multipart_field=["name=value"],
            content_type=None,
        )

        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            open_cloud_request.read_request_body(args)

    def test_multipart_content_type_cannot_be_overridden(self) -> None:
        args = argparse.Namespace(
            data_file=None,
            multipart_file=["files=thumbnail.png"],
            multipart_field=[],
            content_type="multipart/form-data; boundary=unsafe",
        )

        with self.assertRaisesRegex(ValueError, "generated automatically"):
            open_cloud_request.read_request_body(args)

    def test_hand_built_multipart_body_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            body_path = Path(directory, "request.multipart")
            body_path.write_bytes(b"unsafe")
            args = argparse.Namespace(
                data_file=str(body_path),
                multipart_file=[],
                multipart_field=[],
                content_type="multipart/form-data; boundary=manual",
            )

            with self.assertRaisesRegex(ValueError, "Use multipart options"):
                open_cloud_request.read_request_body(args)

    def test_raw_body_defaults_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            body_path = Path(directory, "request.json")
            body_path.write_bytes(b'{"ok":true}')
            args = argparse.Namespace(
                data_file=str(body_path),
                multipart_file=[],
                multipart_field=[],
                content_type=None,
            )

            body, content_type = open_cloud_request.read_request_body(args)

        self.assertEqual(body, b'{"ok":true}')
        self.assertEqual(content_type, "application/json")


def request_args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "method": "POST",
        "url": "https://apis.roblox.com/developer-products/v2/universes/1/developer-products",
        "required_scope": ["developer-product:write"],
        "data_file": None,
        "content_type": None,
        "multipart_file": [],
        "multipart_field": [],
        "apply": False,
        "accept": "application/json",
        "output": None,
        "timeout": 5.0,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class FakeResponse:
    status = 200

    def __init__(self, body: bytes) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class WorkingDirectoryTestCase(unittest.TestCase):
    """Run each test in an empty directory with the key variable unset."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        previous = Path.cwd()
        os.chdir(self.directory)
        self.addCleanup(os.chdir, previous)
        environment = mock.patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop(open_cloud_request.API_KEY_ENV, None)


class CredentialSourceTests(WorkingDirectoryTestCase):
    def test_dotenv_in_working_directory_supplies_the_key(self) -> None:
        Path(".env").write_text(
            "# comment\nOTHER=1\nexport ROBLOX_OPEN_CLOUD_API_KEY=\"quoted-key\"\n",
            encoding="utf-8",
        )

        self.assertEqual(open_cloud_request.credential(), ("quoted-key", ".env"))

    def test_unquoted_value_drops_trailing_comment(self) -> None:
        Path(".env").write_text("ROBLOX_OPEN_CLOUD_API_KEY=plain-key  # note\n", encoding="utf-8")

        self.assertEqual(open_cloud_request.credential(), ("plain-key", ".env"))

    def test_environment_variable_wins_over_dotenv(self) -> None:
        Path(".env").write_text("ROBLOX_OPEN_CLOUD_API_KEY=file-key\n", encoding="utf-8")
        os.environ[open_cloud_request.API_KEY_ENV] = "env-key"

        self.assertEqual(open_cloud_request.credential(), ("env-key", "environment"))

    def test_dotenv_in_a_parent_directory_is_not_read(self) -> None:
        child = self.directory / "child"
        child.mkdir()
        Path(".env").write_text("ROBLOX_OPEN_CLOUD_API_KEY=parent-key\n", encoding="utf-8")
        os.chdir(child)

        self.assertEqual(open_cloud_request.credential(), (None, None))

    def test_byte_order_mark_does_not_hide_the_first_line(self) -> None:
        Path(".env").write_bytes("\ufeffROBLOX_OPEN_CLOUD_API_KEY=bom-key\n".encode("utf-8"))

        self.assertEqual(open_cloud_request.credential(), ("bom-key", ".env"))

    def test_empty_value_counts_as_missing(self) -> None:
        Path(".env").write_text("ROBLOX_OPEN_CLOUD_API_KEY=\n", encoding="utf-8")

        self.assertEqual(open_cloud_request.credential(), (None, None))


class ApplyGateTests(WorkingDirectoryTestCase):
    def test_mutation_without_apply_prints_plan_and_sends_nothing(self) -> None:
        stdout = io.StringIO()
        args = request_args(multipart_field=["name=Gem pack", "price=25"])
        with mock.patch.object(open_cloud_request, "open_request") as open_request, mock.patch.object(
            open_cloud_request.sys, "stdout", stdout
        ):
            status = open_cloud_request.request_command(args)

        self.assertEqual(status, 0)
        open_request.assert_not_called()
        plan = json.loads(stdout.getvalue())
        self.assertFalse(plan["applied"])
        self.assertFalse(plan["credential_configured"])
        self.assertEqual(plan["content_type"], "multipart/form-data")
        self.assertEqual(
            plan["multipart_fields"],
            [{"name": "name", "value": "Gem pack"}, {"name": "price", "value": "25"}],
        )

    def test_mutation_with_apply_sends_the_key_in_the_header(self) -> None:
        Path(".env").write_text("ROBLOX_OPEN_CLOUD_API_KEY=file-key\n", encoding="utf-8")
        output = self.directory / "response.json"
        args = request_args(apply=True, output=str(output))
        with mock.patch.object(
            open_cloud_request, "open_request", return_value=FakeResponse(b"{}")
        ) as open_request, mock.patch.object(open_cloud_request.sys, "stderr", io.StringIO()):
            status = open_cloud_request.request_command(args)

        self.assertEqual(status, 0)
        request = open_request.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("X-api-key"), "file-key")

    def test_abbreviated_apply_flag_is_rejected(self) -> None:
        parser = open_cloud_request.build_parser()
        base = ["request", "--method", "POST", "--url", "https://apis.roblox.com/x", "--required-scope", "s"]
        for flag in ("--ap", "--app", "--appl"):
            with self.subTest(flag=flag), self.assertRaises(SystemExit), mock.patch.object(
                open_cloud_request.sys, "stderr", io.StringIO()
            ):
                parser.parse_args([*base, flag])

        self.assertTrue(parser.parse_args([*base, "--apply"]).apply)

    def test_get_is_sent_without_apply(self) -> None:
        os.environ[open_cloud_request.API_KEY_ENV] = "env-key"
        output = self.directory / "response.json"
        args = request_args(method="GET", required_scope=["developer-product:read"], output=str(output))
        with mock.patch.object(
            open_cloud_request, "open_request", return_value=FakeResponse(b"[]")
        ) as open_request, mock.patch.object(open_cloud_request.sys, "stderr", io.StringIO()):
            status = open_cloud_request.request_command(args)

        self.assertEqual(status, 0)
        open_request.assert_called_once()
        self.assertEqual(output.read_bytes(), b"[]")


class IntrospectTests(WorkingDirectoryTestCase):
    def test_key_travels_only_in_the_body_and_is_redacted_from_the_response(self) -> None:
        Path(".env").write_text("ROBLOX_OPEN_CLOUD_API_KEY=file-key\n", encoding="utf-8")
        output = self.directory / "introspect.json"
        args = argparse.Namespace(output=str(output), timeout=5.0)
        response = FakeResponse(b'{"name":"dev","echo":"file-key","scopes":[]}')
        with mock.patch.object(open_cloud_request, "open_request", return_value=response) as open_request, mock.patch.object(
            open_cloud_request.sys, "stderr", io.StringIO()
        ):
            status = open_cloud_request.introspect_command(args)

        self.assertEqual(status, 0)
        request = open_request.call_args.args[0]
        self.assertEqual(request.full_url, "https://apis.roblox.com/api-keys/v1/introspect")
        self.assertIsNone(request.get_header("X-api-key"))
        self.assertEqual(json.loads(request.data), {"apiKey": "file-key"})
        self.assertNotIn(b"file-key", output.read_bytes())

    def test_missing_key_stops_before_sending(self) -> None:
        args = argparse.Namespace(output=None, timeout=5.0)
        with mock.patch.object(open_cloud_request, "open_request") as open_request, mock.patch.object(
            open_cloud_request.sys, "stderr", io.StringIO()
        ):
            status = open_cloud_request.introspect_command(args)

        self.assertEqual(status, 2)
        open_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
