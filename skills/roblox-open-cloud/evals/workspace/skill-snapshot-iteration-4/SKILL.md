---
name: roblox-open-cloud
description: Securely call Roblox Open Cloud REST APIs with API-key authentication while keeping the credential hidden from the agent, command arguments, logs, and chat. Use this skill whenever a Roblox task asks to call, query, invoke, automate, publish through, or troubleshoot Open Cloud or a Roblox web API under apis.roblox.com—even when the user says only “Roblox API” or names a resource such as Data Stores, Memory Stores, Messaging, assets, places, universes, or webhooks. Do not use it for in-experience Roblox engine APIs, Studio scripting, Creator Dashboard UI-only work, or OAuth user-consent flows.
compatibility: Requires Python 3, HTTPS access to apis.roblox.com, and ROBLOX_OPEN_CLOUD_API_KEY in the agent process environment.
---

# Roblox Open Cloud

Call Roblox Open Cloud without making the API key visible to the model. The bundled helper is the only credential boundary: it reads the environment variable inside its own process, adds `x-api-key`, blocks untrusted destinations and redirects, and redacts the credential from response/error output.

Resolve every relative path below from this skill directory.

## Credential gate

Run this before researching or constructing a request:

```bash
python3 scripts/open_cloud_request.py check --open-on-missing
```

The command reports only whether `ROBLOX_OPEN_CLOUD_API_KEY` is non-empty; it never returns the value.

If it reports `configured: false`:

1. The helper opens <https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab>.
2. Ask the user to create a least-privilege API key and set `ROBLOX_OPEN_CLOUD_API_KEY` in the environment inherited by the agent process.
3. Tell the user not to paste the key into chat, a command argument, source code, a repository, or a file the agent can read.
4. Stop. Do not inspect other environment variables, accept the key through chat/stdin/a flag, or attempt the API call.

A key exported in a different terminal after this agent started might not reach the current process. In that case, ask the user to restart or relaunch the agent from the configured environment.

## Request workflow

After the gate succeeds:

1. Read the current official Roblox Open Cloud operation documentation. Confirm the HTTP method, exact `https://apis.roblox.com/...` path, query parameters, body schema, every required permission scope, resource restrictions, and success response. Never infer an endpoint or scope from memory.
2. State the exact documented scope names before the request. Pass each scope to the helper with a separate `--required-scope`; this lets failures carry actionable permission guidance without inspecting the key.
3. For a mutation, state the target resource and intended effect before execution. If the user's request already clearly authorizes that exact mutation, proceed; otherwise request confirmation.
4. Put JSON request bodies in a temporary file outside the repository. Never put credentials in that file.
5. Execute only through the helper. Do not use raw `curl`, HTTP libraries in ad-hoc code, browser JavaScript, Roblox Studio HTTP tools, or shell interpolation of the key.
6. Interpret status codes from the operation contract. `401` usually means a missing or invalid key. On `403`, report every documented required scope by its exact identifier, include the literal API Key management URL `https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab`, and ask the user to verify the selected API system/operations, target experience or resource restrictions, accepted IP addresses, and key status. The literal URL makes the remediation directly actionable; a bare “Creator Dashboard” mention is insufficient. Do not ask the user to reveal the key.
7. For mutations, perform the documented read-back when one exists and report the observed result separately from the initial response.
8. Remove temporary request/response files containing user data when they are no longer needed. Do not delete user-authored files.

## Helper commands

Check credential presence:

```bash
python3 scripts/open_cloud_request.py check --open-on-missing
```

GET request, printing the response body:

```bash
python3 scripts/open_cloud_request.py request \
  --method GET \
  --url 'https://apis.roblox.com/EXACT_DOCUMENTED_PATH' \
  --required-scope 'EXACT_DOCUMENTED_SCOPE'
```

JSON mutation using a body file:

```bash
python3 scripts/open_cloud_request.py request \
  --method POST \
  --url 'https://apis.roblox.com/EXACT_DOCUMENTED_PATH' \
  --required-scope 'EXACT_DOCUMENTED_WRITE_SCOPE' \
  --content-type 'application/json' \
  --data-file /tmp/roblox-open-cloud-request.json
```

Save a response without printing its body:

```bash
python3 scripts/open_cloud_request.py request \
  --method GET \
  --url 'https://apis.roblox.com/EXACT_DOCUMENTED_PATH' \
  --required-scope 'EXACT_DOCUMENTED_SCOPE' \
  --output /tmp/roblox-open-cloud-response.json
```

The helper accepts `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`; only `https://apis.roblox.com` is allowed. Repeat `--required-scope` when an operation requires multiple scopes. The helper reports those scopes and the credential dashboard on `403`. It does not follow redirects because forwarding an authenticated header to a redirected destination can leak a credential.

## Credential safety boundary

- Never read, print, return, summarize, compare, validate, introspect, or count characters in the API key.
- Never run `printenv`, `env`, shell expansion such as `$ROBLOX_OPEN_CLOUD_API_KEY`, or any command that can expose the value in arguments, logs, history, process listings, or tool input.
- Never add an alternate path that accepts an API key by option, stdin, request body, config file, or source file.
- Never call the API-key introspection endpoint: its request body would expose the key outside the helper's header-only boundary.
- Never send the key to non-Roblox hosts. Do not weaken the helper host, HTTPS, or redirect checks to make an endpoint work.
- Report only `configured: true/false`, HTTP status, sanitized response body or output path, and actionable permission/resource guidance.

## Key creation guidance

When setup is required, point the user to the Creator Dashboard page already opened by the helper. Recommend a separate key per automation, the minimum operation scopes, restriction to the specific experience/resources where supported, an IP restriction when the caller has a stable IP, and an expiration/rotation policy appropriate to the automation. For group automation, recommend a dedicated account with only the required group role.

Official references:

- API key management: <https://create.roblox.com/docs/cloud/auth/api-keys>
- Open Cloud overview/reference: <https://create.roblox.com/docs/cloud>
- Credential dashboard: <https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab>

## Result format

Keep the response concise:

Write prose and field labels in the same language as the user's latest request. Keep exact scope identifiers, URLs, HTTP tokens, and JSON fields untranslated. The template below defines the information to include, not mandatory English labels.

```text
Credential: configured | missing
Request: METHOD https://apis.roblox.com/…
Result: HTTP <status> — <documented meaning>
Required permissions: <exact documented scopes; always include on 403>
Verification: <read-back result, not applicable, or not performed>
Next: <on 403, literal https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab plus resource/IP/key-status checks; otherwise only if action is required>
```

Never include request headers, the key, or a command containing the key.
