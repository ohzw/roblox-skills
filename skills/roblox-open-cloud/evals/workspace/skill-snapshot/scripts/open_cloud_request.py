#!/usr/bin/env python3
"""Call Roblox Open Cloud without exposing its API key to the invoking agent."""

from __future__ import annotations

import argparse
import json
import os
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
        body = read_body(args.data_file)
        if body is not None and method == "GET":
            raise ValueError("GET requests cannot include a body")

        headers = {
            "Accept": args.accept,
            "User-Agent": "roblox-open-cloud-skill/1",
            "x-api-key": key,
        }
        if body is not None:
            headers["Content-Type"] = args.content_type

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
        emit_json(
            {
                "ok": False,
                "status": error.code,
                "method": args.method.upper(),
                "url": args.url,
                "error": "http_error",
            },
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
    request_parser.add_argument("--data-file")
    request_parser.add_argument("--content-type", default="application/json")
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
