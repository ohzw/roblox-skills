#!/usr/bin/env python3

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import open_cloud_request


class MultipartBodyTests(unittest.TestCase):
    def test_repeated_file_field_builds_valid_multipart_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory, "first.png")
            second = Path(directory, "second.jpg")
            first.write_bytes(b"first-image")
            second.write_bytes(b"second-image")

            with mock.patch.object(open_cloud_request.secrets, "token_hex", return_value="fixed"):
                body, content_type = open_cloud_request.build_multipart_body(
                    [f"files={first}", f"files={second}"]
                )

        self.assertEqual(
            content_type,
            "multipart/form-data; boundary=roblox-open-cloud-fixed",
        )
        self.assertEqual(body.count(b'name="files"'), 2)
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
            content_type=None,
        )

        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            open_cloud_request.read_request_body(args)

    def test_multipart_content_type_cannot_be_overridden(self) -> None:
        args = argparse.Namespace(
            data_file=None,
            multipart_file=["files=thumbnail.png"],
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
                content_type="multipart/form-data; boundary=manual",
            )

            with self.assertRaisesRegex(ValueError, "Use --multipart-file"):
                open_cloud_request.read_request_body(args)

    def test_raw_body_defaults_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            body_path = Path(directory, "request.json")
            body_path.write_bytes(b'{"ok":true}')
            args = argparse.Namespace(
                data_file=str(body_path),
                multipart_file=[],
                content_type=None,
            )

            body, content_type = open_cloud_request.read_request_body(args)

        self.assertEqual(body, b'{"ok":true}')
        self.assertEqual(content_type, "application/json")


if __name__ == "__main__":
    unittest.main()
