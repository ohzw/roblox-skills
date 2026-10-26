#!/usr/bin/env python3
"""Call Roblox Open Cloud without exposing its API key to the invoking agent."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import secrets
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_KEY_ENV = "ROBLOX_OPEN_CLOUD_API_KEY"
DOTENV_NAME = ".env"
CREDENTIALS_URL = "https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab"
INTROSPECT_URL = "https://apis.roblox.com/api-keys/v1/introspect"
ALLOWED_HOST = "apis.roblox.com"
ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
MAX_ERROR_BODY_BYTES = 1_048_576
USER_AGENT = "roblox-open-cloud-skill/1"
DOTENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "Redirect blocked", headers, fp)


def emit_json(payload: dict[str, object], *, stream=None) -> None:  # noqa: ANN001
    stream = stream or sys.stdout
    json.dump(payload, stream, ensure_ascii=False)
    stream.write("\n")


def dotenv_value(path: Path, name: str) -> str | None:
    """Read one variable from a dotenv file; the last assignment wins."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None
    found = None
    for line in text.splitlines():
        match = DOTENV_LINE.match(line)
        if match is None or match.group(1) != name:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value).strip()
        found = value or None
    return found


def dotenv_path() -> Path:
    return Path.cwd() / DOTENV_NAME


def credential() -> tuple[str | None, str | None]:
    """Return the key and where it came from: the environment first, then ./.env."""
    value = os.environ.get(API_KEY_ENV)
    if value:
        return value, "environment"
    value = dotenv_value(dotenv_path(), API_KEY_ENV)
    if value:
        return value, DOTENV_NAME
    return None, None


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
    key, source = credential()
    configured = key is not None
    opened = False
    if not configured and args.open_on_missing:
        opened = open_credentials_page()
    emit_json(
        {
            "configured": configured,
            "source": source,
            "environment_variable": API_KEY_ENV,
            "dotenv_file": str(dotenv_path()),
            "credentials_page_opened": opened,
            "credentials_url": CREDENTIALS_URL if not configured else None,
        }
    )
    return 0 if configured else 2


def report_missing_credential() -> int:
    emit_json(
        {
            "error": "credential_missing",
            "configured": False,
            "environment_variable": API_KEY_ENV,
            "dotenv_file": str(dotenv_path()),
            "credentials_url": CREDENTIALS_URL,
        },
        stream=sys.stderr,
    )
    return 2


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


def open_request(request: urllib.request.Request, timeout: float):  # noqa: ANN201
    opener = urllib.request.build_opener(
        NoRedirectHandler(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return opener.open(request, timeout=timeout)


def send(
    request: urllib.request.Request,
    key: str,
    *,
    required_scopes: list[str],
    output: str | None,
    timeout: float,
) -> int:
    method = request.get_method()
    url = request.full_url
    try:
        with open_request(request, timeout) as response:
            response_body = redact(response.read(), key)
            write_response(response_body, output)
            emit_json(
                {
                    "ok": True,
                    "status": response.status,
                    "method": method,
                    "url": url,
                    "required_scopes": required_scopes,
                    "output": output,
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
            "method": method,
            "url": url,
            "error": "http_error",
            "required_scopes": required_scopes,
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
                "required_scopes": required_scopes,
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
        emit_json(error_result, stream=sys.stderr)
        return 1
    except (OSError, urllib.error.URLError) as error:
        return report_local_error(method, url, error)


def report_local_error(method: str, url: str, error: Exception) -> int:
    emit_json(
        {
            "ok": False,
            "method": method.upper(),
            "url": url,
            "error": type(error).__name__,
            "message": str(error),
        },
        stream=sys.stderr,
    )
    return 1


def dry_run_plan(
    args: argparse.Namespace,
    method: str,
    url: str,
    body: bytes | None,
    content_type: str | None,
    configured: bool,
) -> dict[str, object]:
    return {
        "applied": False,
        "method": method,
        "url": url,
        "required_scopes": args.required_scope,
        "content_type": content_type.partition(";")[0] if content_type else None,
        "body_bytes": len(body) if body is not None else 0,
        "multipart_fields": [
            {"name": field, "value": value} for field, value in map(parse_multipart_field, args.multipart_field)
        ],
        "data_file": args.data_file,
        "multipart_files": [
            {"name": field, "file": str(path)} for field, path in map(parse_multipart_file, args.multipart_file)
        ],
        "credential_configured": configured,
        "next": "Nothing was sent. Show this plan, confirm the mutation, then rerun the same command with --apply.",
    }


def request_command(args: argparse.Namespace) -> int:
    try:
        method = args.method.upper()
        if method not in ALLOWED_METHODS:
            raise ValueError(f"Unsupported method: {method}")
        url = validate_url(args.url)
        body, content_type = read_request_body(args)
        if body is not None and method == "GET":
            raise ValueError("GET requests cannot include a body")
    except (OSError, ValueError) as error:
        return report_local_error(args.method, args.url, error)

    key, _ = credential()
    if method != "GET" and not args.apply:
        emit_json(dry_run_plan(args, method, url, body, content_type, key is not None))
        return 0
    if key is None:
        return report_missing_credential()

    headers = {
        "Accept": args.accept,
        "User-Agent": USER_AGENT,
        "x-api-key": key,
    }
    if content_type is not None:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    return send(request, key, required_scopes=args.required_scope, output=args.output, timeout=args.timeout)


def introspect_command(args: argparse.Namespace) -> int:
    key, _ = credential()
    if key is None:
        return report_missing_credential()
    request = urllib.request.Request(
        INTROSPECT_URL,
        data=json.dumps({"apiKey": key}).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    return send(request, key, required_scopes=[], output=args.output, timeout=args.timeout)


def build_parser() -> argparse.ArgumentParser:
    # Abbreviations are off so `--apply` must appear literally; callers gate approvals on that exact flag.
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check", help="Report credential presence without reading it out", allow_abbrev=False
    )
    check_parser.add_argument("--open-on-missing", action="store_true")
    check_parser.set_defaults(handler=check_command)

    request_parser = subparsers.add_parser(
        "request", help="Send an authenticated Open Cloud request", allow_abbrev=False
    )
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
    request_parser.add_argument(
        "--apply",
        action="store_true",
        help="Send a non-GET request; without it the request is only validated and printed",
    )
    request_parser.add_argument("--accept", default="application/json")
    request_parser.add_argument("--output")
    request_parser.add_argument("--timeout", type=float, default=30.0)
    request_parser.set_defaults(handler=request_command)

    introspect_parser = subparsers.add_parser(
        "introspect",
        help="Show the configured key's scopes, targets, and status via the official introspection endpoint",
        allow_abbrev=False,
    )
    introspect_parser.add_argument("--output")
    introspect_parser.add_argument("--timeout", type=float, default=30.0)
    introspect_parser.set_defaults(handler=introspect_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
