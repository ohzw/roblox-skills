#!/usr/bin/env python3
"""Query Roblox's official OpenAPI document without handling credentials."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

OPENAPI_URL = "https://create.roblox.com/docs/cloud/openapi.json"
EXPECTED_HOST = "create.roblox.com"
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
STOP_WORDS = {"a", "an", "and", "api", "for", "of", "the", "to"}
TOKEN_ALIASES = {
    "assets": "asset",
    "entries": "entry",
    "listed": "list",
    "listing": "list",
    "saved": "save",
    "saves": "save",
    "saving": "save",
    "stores": "store",
    "universes": "universe",
}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def emit(payload: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, ensure_ascii=False, indent=2)
    stream.write("\n")


def load_document(timeout: float) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(OPENAPI_URL)
    if parsed.scheme != "https" or parsed.hostname != EXPECTED_HOST:
        raise ValueError("Unexpected OpenAPI source URL")

    request = urllib.request.Request(OPENAPI_URL, headers={"Accept": "application/json"})
    opener = urllib.request.build_opener(NoRedirectHandler(), urllib.request.HTTPSHandler())
    with opener.open(request, timeout=timeout) as response:
        final_url = urllib.parse.urlsplit(response.geturl())
        if final_url.scheme != "https" or final_url.hostname != EXPECTED_HOST:
            raise ValueError("OpenAPI source redirected outside create.roblox.com")
        data = response.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("OpenAPI document exceeds safety limit")
    document = json.loads(data)
    if not isinstance(document, dict) or not isinstance(document.get("paths"), dict):
        raise ValueError("OpenAPI document has no paths object")
    return document


def resolve_pointer(document: dict[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        return None
    current: Any = document
    for raw_segment in reference[2:].split("/"):
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def component_references(value: Any) -> list[str]:
    references: set[str] = set()

    def collect(child: Any) -> None:
        if isinstance(child, dict):
            reference = child.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/components/"):
                references.add(reference)
            for nested in child.values():
                collect(nested)
        elif isinstance(child, list):
            for nested in child:
                collect(nested)

    collect(value)
    return sorted(references)


def direct_referenced_components(document: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    return {
        reference: value
        for reference in component_references(operation)
        if (value := resolve_pointer(document, reference)) is not None
    }


def operation_summary(path: str, method: str, operation: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path,
        "method": method.upper(),
        "summary": operation.get("summary"),
        "operation_id": operation.get("operationId"),
        "tags": operation.get("tags", []),
        "scopes": operation.get("x-roblox-scopes", []),
        "stability": operation.get("x-roblox-stability"),
        "deprecated": operation.get("x-roblox-deprecated", operation.get("deprecated", False)),
        "alternatives": operation.get("x-roblox-alternatives", []),
        "rate_limits": operation.get("x-roblox-rate-limits"),
        "engine_usability": operation.get("x-roblox-engine-usability"),
        "external_docs": operation.get("externalDocs"),
    }


def normalized_tokens(value: str) -> list[str]:
    return [
        TOKEN_ALIASES.get(token, token)
        for token in re.findall(r"[a-z0-9:_-]+", value.casefold())
        if token not in STOP_WORDS
    ]


def normalized_text(value: str) -> str:
    return " ".join(normalized_tokens(value))


def search(
    document: dict[str, Any],
    query: str,
    limit: int,
    method_filter: str | None,
    required_terms: list[str],
) -> dict[str, Any]:
    normalized_query = normalized_text(query)
    tokens = normalized_tokens(query)
    normalized_requirements = [normalized_text(term) for term in required_terms]
    candidates: list[tuple[int, str, str, dict[str, Any]]] = []
    for path, path_item in document["paths"].items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            if method_filter is not None and method != method_filter.casefold():
                continue
            identity = " ".join(
                [
                    path,
                    str(operation.get("summary", "")),
                    str(operation.get("operationId", "")),
                    " ".join(str(tag) for tag in operation.get("tags", [])),
                ]
            )
            searchable = f"{identity} {operation.get('description', '')}"
            normalized_identity = normalized_text(identity)
            normalized_searchable = normalized_text(searchable)
            if any(requirement not in normalized_identity for requirement in normalized_requirements):
                continue
            score = 100 if normalized_query and normalized_query in normalized_searchable else 0
            normalized_path = normalized_text(path)
            for token in tokens:
                if token in normalized_searchable:
                    score += 10
                if token in normalized_path:
                    score += 3
            if score > 0:
                candidates.append((score, path, method, operation))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    return {
        "found": bool(candidates),
        "source": OPENAPI_URL,
        "openapi": document.get("openapi"),
        "server": document.get("servers", [{}])[0].get("url"),
        "query": query,
        "method_filter": method_filter.upper() if method_filter else None,
        "required_terms": required_terms,
        "candidates": [
            {"score": score, **operation_summary(path, method, operation)}
            for score, path, method, operation in candidates[:limit]
        ],
        "fallback_required": not candidates,
    }


def get_operation(document: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    path_item = document["paths"].get(path)
    operation = path_item.get(method.lower()) if isinstance(path_item, dict) else None
    if not isinstance(operation, dict):
        return {
            "found": False,
            "source": OPENAPI_URL,
            "openapi": document.get("openapi"),
            "path": path,
            "method": method.upper(),
            "fallback_required": True,
            "fallback": "Use the current official feature or domain reference; do not infer the contract.",
        }
    return {
        "found": True,
        "source": OPENAPI_URL,
        "openapi": document.get("openapi"),
        "extensions_version": document.get("info", {}).get("x-roblox-extensions-version"),
        "server": document.get("servers", [{}])[0].get("url"),
        **operation_summary(path, method, operation),
        "description": operation.get("description"),
        "parameters": operation.get("parameters", []),
        "request_body": operation.get("requestBody"),
        "responses": operation.get("responses", {}),
        "security": operation.get("security", []),
        "referenced_components": direct_referenced_components(document, operation),
        "nested_component_references_omitted": True,
        "fallback_required": False,
    }
def get_component(document: dict[str, Any], reference: str) -> dict[str, Any]:
    value = resolve_pointer(document, reference)
    if value is None or not reference.startswith("#/components/"):
        return {
            "found": False,
            "source": OPENAPI_URL,
            "openapi": document.get("openapi"),
            "reference": reference,
        }
    return {
        "found": True,
        "source": OPENAPI_URL,
        "openapi": document.get("openapi"),
        "reference": reference,
        "schema": value,
        "nested_references": component_references(value),
    }



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query the official Roblox OpenAPI document")
    parser.add_argument("--timeout", type=float, default=30.0)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Find candidate operations")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--method", choices=sorted(method.upper() for method in HTTP_METHODS))
    search_parser.add_argument("--required-term", action="append", default=[])
    search_parser.add_argument("--limit", type=int, default=8)

    operation_parser = subparsers.add_parser("operation", help="Read one exact operation and its direct components")
    operation_parser.add_argument("--method", required=True, choices=sorted(method.upper() for method in HTTP_METHODS))
    operation_parser.add_argument("--path", required=True)

    component_parser = subparsers.add_parser("component", help="Read one exact component reference")
    component_parser.add_argument("--reference", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        document = load_document(args.timeout)
        if args.command == "search":
            emit(
                search(
                    document,
                    args.query,
                    max(1, min(args.limit, 25)),
                    args.method,
                    args.required_term,
                )
            )
        elif args.command == "operation":
            if not args.path.startswith("/"):
                raise ValueError("--path must be an OpenAPI path beginning with /")
            emit(get_operation(document, args.path, args.method))
        else:
            emit(get_component(document, args.reference))
        return 0
    except Exception as error:
        emit({"ok": False, "source": OPENAPI_URL, "error": type(error).__name__, "message": str(error)}, stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
