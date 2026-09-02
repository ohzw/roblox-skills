#!/usr/bin/env python3
"""Call Roblox Open Cloud without exposing its API key to the invoking agent."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import secrets
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_KEY_ENV = "ROBLOX_OPEN_CLOUD_API_KEY"
CREDENTIALS_URL = "https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab"
ALLOWED_HOST = "apis.roblox.com"
ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
MAX_ERROR_BODY_BYTES = 1_048_576


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "Redirect blocked", headers, fp)


def emit_json(payload: dict[str, object], *, stream=sys.stdout) -> None:
    json.dump(payload, stream, ensure_ascii=False)
    stream.write("\n")


def credential() -> str | None:
    value = os.environ.get(API_KEY_ENV)
    return value if value else None


def open_credentials_page() -> bool:
    try:
        completed = subprocess.run(
            ["open", CREDENTIALS_URL],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return completed.returncode == 0


def check_command(args: argparse.Namespace) -> int:
    configured = credential() is not None
    opened = False
    if not configured and args.open_on_missing:
        opened = open_credentials_page()
    emit_json(
        {
            "configured": configured,
            "environment_variable": API_KEY_ENV,
            "credentials_page_opened": opened,
            "credentials_url": CREDENTIALS_URL if not configured else None,
        }
    )
    return 0 if configured else 2


def validate_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS URLs are allowed")
    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(f"Only {ALLOWED_HOST} is allowed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials in URLs are not allowed")
    if parsed.port not in (None, 443):
        raise ValueError("Only the default HTTPS port is allowed")
    if parsed.fragment:
        raise ValueError("URL fragments are not sent to APIs and are not allowed")
    return urllib.parse.urlunsplit(parsed)


def read_body(path_value: str | None) -> bytes | None:
    if path_value is None:
        return None
    path = Path(path_value)
    if not path.is_file():
        raise ValueError(f"Request body file does not exist: {path}")
    return path.read_bytes()


def parse_multipart_file(value: str) -> tuple[str, Path]:
    field, separator, path_value = value.partition("=")
    if not separator or not field or not path_value:
        raise ValueError("Multipart files must use FIELD=PATH")
    if any(character in field for character in '\r\n"'):
        raise ValueError("Multipart field names cannot contain quotes or line breaks")
    path = Path(path_value)
    if not path.is_file():
        raise ValueError(f"Multipart file does not exist: {path}")
    if any(character in path.name for character in "\r\n"):
        raise ValueError("Multipart filenames cannot contain line breaks")
    return field, path


def parse_multipart_field(value: str) -> tuple[str, str]:
    field, separator, field_value = value.partition("=")
    if not separator or not field:
        raise ValueError("Multipart fields must use FIELD=VALUE")
    if any(character in field for character in '\r\n"'):
        raise ValueError("Multipart field names cannot contain quotes or line breaks")
    return field, field_value


def quote_multipart_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_multipart_body(files: list[str], fields: list[str]) -> tuple[bytes, str]:
    boundary = f"roblox-open-cloud-{secrets.token_hex(24)}"
    body = bytearray()
    for value in fields:
        field, field_value = parse_multipart_field(value)
        body.extend(f"--{boundary}\r\n".encode("ascii"))
        body.extend(f'Content-Disposition: form-data; name="{quote_multipart_value(field)}"\r\n\r\n'.encode("utf-8"))
        body.extend(field_value.encode("utf-8"))
        body.extend(b"\r\n")
    for value in files:
        field, path = parse_multipart_file(value)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("ascii"))
        body.extend(
            (
                'Content-Disposition: form-data; '
                f'name="{quote_multipart_value(field)}"; '
                f'filename="{quote_multipart_value(path.name)}"\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("ascii"))
        body.extend(path.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("ascii"))
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def read_request_body(args: argparse.Namespace) -> tuple[bytes | None, str | None]:
    if args.data_file is not None and (args.multipart_file or args.multipart_field):
        raise ValueError("--data-file and multipart options are mutually exclusive")
    if args.multipart_file or args.multipart_field:
        if args.content_type is not None:
            raise ValueError("--content-type is generated automatically for multipart requests")
        return build_multipart_body(args.multipart_file, args.multipart_field)
    body = read_body(args.data_file)
    if body is None:
        return None, None
    content_type = args.content_type or "application/json"
    if content_type.partition(";")[0].strip().lower() == "multipart/form-data":
        raise ValueError("Use multipart options instead of a hand-built multipart body")
    return body, content_type


def redact(data: bytes, secret: str) -> bytes:
    secret_bytes = secret.encode("utf-8")
    return data.replace(secret_bytes, b"[REDACTED]") if secret_bytes else data


def write_response(data: bytes, output: str | None) -> None:
    if output is None:
        sys.stdout.buffer.write(data)
        if data and not data.endswith(b"\n"):
            sys.stdout.buffer.write(b"\n")
        return
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def request_command(args: argparse.Namespace) -> int:
    key = credential()
    if key is None:
        emit_json(
            {
                "error": "credential_missing",
                "configured": False,
                "environment_variable": API_KEY_ENV,
                "credentials_url": CREDENTIALS_URL,
            },
            stream=sys.stderr,
        )
        return 2

    try:
        method = args.method.upper()
        if method not in ALLOWED_METHODS:
            raise ValueError(f"Unsupported method: {method}")
        url = validate_url(args.url)
        body, content_type = read_request_body(args)
        if body is not None and method == "GET":
            raise ValueError("GET requests cannot include a body")

        headers = {
            "Accept": args.accept,
            "User-Agent": "roblox-open-cloud-skill/1",
            "x-api-key": key,
        }
        if content_type is not None:
            headers["Content-Type"] = content_type

        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        opener = urllib.request.build_opener(
            NoRedirectHandler(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )
        with opener.open(request, timeout=args.timeout) as response:
            response_body = redact(response.read(), key)
            write_response(response_body, args.output)
            emit_json(
                {
                    "ok": True,
                    "status": response.status,
                    "method": method,
                    "url": url,
                    "required_scopes": args.required_scope,
                    "output": args.output,
                },
                stream=sys.stderr,
            )
            return 0
    except urllib.error.HTTPError as error:
        error_body = redact(error.read(MAX_ERROR_BODY_BYTES), key)
        if error_body:
            sys.stderr.buffer.write(error_body)
            if not error_body.endswith(b"\n"):
                sys.stderr.buffer.write(b"\n")
        error_result: dict[str, object] = {
            "ok": False,
            "status": error.code,
            "method": args.method.upper(),
            "url": args.url,
            "error": "http_error",
            "required_scopes": args.required_scope,
        }
        error_result["credential_present"] = True
        if error.code == 401:
            error_result["problem"] = "authentication"
            error_result["credential_guidance"] = {
                "action": "verify the existing key status and expiration; regenerate only if invalid",
                "do_not_claim": "credential missing or environment variable unset",
                "credentials_url": CREDENTIALS_URL,
            }
        if error.code == 403:
            error_result["problem"] = "authorization"
            error_result["permission_guidance"] = {
                "required_scopes": args.required_scope,
                "credentials_url": CREDENTIALS_URL,
                "action": "edit permissions or restrictions on the existing configured key",
                "do_not_suggest": [
                    "create a new key",
                    "set or re-enter the environment variable",
                    "restart the agent",
                ],
                "verify": [
                    "selected API system and operations",
                    "target experience or resource restrictions",
                    "accepted IP addresses",
                    "key status and expiration",
                ],
            }
        emit_json(
            error_result,
            stream=sys.stderr,
        )
        return 1
    except (OSError, ValueError, urllib.error.URLError) as error:
        emit_json(
            {
                "ok": False,
                "method": args.method.upper(),
                "url": args.url,
                "error": type(error).__name__,
                "message": str(error),
            },
            stream=sys.stderr,
        )
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Report credential presence without reading it out")
    check_parser.add_argument("--open-on-missing", action="store_true")
    check_parser.set_defaults(handler=check_command)

    request_parser = subparsers.add_parser("request", help="Send an authenticated Open Cloud request")
    request_parser.add_argument("--method", required=True)
    request_parser.add_argument("--url", required=True)
    request_parser.add_argument(
        "--required-scope",
        action="append",
        required=True,
        help="Exact documented permission scope; repeat for multiple scopes",
    )
    request_parser.add_argument("--data-file")
    request_parser.add_argument("--content-type")
    request_parser.add_argument(
        "--multipart-file",
        action="append",
        default=[],
        metavar="FIELD=PATH",
        help="Binary multipart field; repeat the option for array fields",
    )
    request_parser.add_argument(
        "--multipart-field",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help="Text multipart field; repeat for multiple form fields",
    )
    request_parser.add_argument("--accept", default="application/json")
    request_parser.add_argument("--output")
    request_parser.add_argument("--timeout", type=float, default=30.0)
    request_parser.set_defaults(handler=request_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
