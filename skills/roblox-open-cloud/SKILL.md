---
name: roblox-open-cloud
description: Securely resolve and call Roblox Open Cloud REST APIs with API-key authentication while keeping the credential hidden from the agent, arguments, logs, and chat. Use this skill whenever a Roblox task asks to call, query, invoke, automate, publish through, plan, or troubleshoot Open Cloud or a Roblox web API under apis.roblox.com. It verifies methods, paths, parameters, schemas, scopes, stability, and responses against Roblox's live official OpenAPI document, with an official-reference fallback for operations missing from that document. Trigger even when the user says only “Roblox API” or names Data Stores, Memory Stores, Messaging, assets, places, universes, Creator Store, or webhooks. Do not use it for in-experience Roblox engine APIs, Studio scripting, Creator Dashboard UI-only work, or OAuth user-consent flows.
compatibility: Requires Python 3, HTTPS access to create.roblox.com and apis.roblox.com, and ROBLOX_OPEN_CLOUD_API_KEY in the agent process environment.
---

# Roblox Open Cloud

Call Roblox Open Cloud without making the API key visible to the model. The bundled request helper is the only credential boundary: it reads the environment variable inside its own process, adds `x-api-key`, blocks untrusted destinations and redirects, and redacts the credential from response/error output. The separate OpenAPI lookup helper reads only Roblox's public specification and never handles credentials.

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

1. Query the current official OpenAPI document before constructing the request:
   - Preserve the user's action, resource, and state qualifiers before searching. Terms such as saved, archived, pending, version, entry, and collection distinguish different resources; dropping one can produce a valid call that answers the wrong task.
   - Apply a method filter only when the operation contract makes the method known. Read-only operations are not necessarily `GET`: searches, analytics queries, calculations, and other side-effect-free actions may use `POST`. If the method is uncertain, search without `--method`, compare candidates by operation semantics, then resolve the selected exact path and method. Determine mutation status from the documented effect, not from the HTTP method alone. Pass distinctive qualifiers with repeated `--required-term` so a generic candidate cannot outrank the requested resource.
   - Search for multiple candidates with `scripts/openapi_lookup.py search`. Compare path, method, summary, operation ID, scopes, and mutation effect. Select a candidate only when all user-requested qualifiers are represented.
   - Prefer the current operation for the requested resource, using `x-roblox-deprecated`, `x-roblox-alternatives`, stability, and the linked reference to distinguish it from obsolete web endpoints. Prefer `/cloud/v2/` when it is the current form of that same resource, but do not classify an OpenAPI-documented service path as legacy merely because it contains `/v1/`; active services also use paths such as `/datastores/v1/` and other service-specific versioned prefixes.
   - Resolve the selected exact path and method with `scripts/openapi_lookup.py operation`. If the user asks for saved Creator Store assets, resolve the `saves` collection; do not substitute general asset search merely because it returns assets.
   - When `found: true`, use the returned method, server, path, parameters, request body, responses, `security`, and referenced schemas as the machine-readable contract. Read `external_docs` as well when present; it carries semantics and constraints that a schema cannot express.
2. Treat `found: false` or `fallback_required: true` as an OpenAPI coverage gap, not evidence that the API does not exist. Read the current official Roblox feature or domain reference and its linked operation section. Record that the contract came from the official-reference fallback. Never invent a path, field, or scope to fill the gap.
3. Cross-check Roblox extensions when present: every entry in `x-roblox-scopes`, its `targetResourceSpecifier` or condition, `x-roblox-stability`, `x-roblox-deprecated`, `x-roblox-alternatives`, `x-roblox-rate-limits`, and `x-roblox-engine-usability`. The OpenAPI page says the document is still under development and most extensions are experimental, so use the current download rather than a cached copy and verify consequential semantics in the linked reference.
4. If the OpenAPI operation and its current official reference disagree on method, path, body, scope, or mutation effect, do not guess. State the conflict and stop before calling the API, especially for mutations.
5. State the exact documented scope names and their source before the request. Note that `--required-scope` is a mandatory option for `open_cloud_request.py request`. Pass each scope with a separate `--required-scope`. If the OpenAPI schema specifies `scopes: []` (empty array), pass a standard domain-appropriate scope (e.g. `universe:read` for Universes/Places read operations) to satisfy helper validation.
6. For a mutation, state the target resource and intended effect before execution. If the user's request already clearly authorizes that exact mutation, proceed; otherwise request confirmation.
7. Preserve the OpenAPI media-type contract and keep generated body artifacts out of the repository:
   - Put generated JSON and raw binary bodies in a temporary file outside the repository and pass it with `--data-file` plus the exact documented `--content-type`.
   - For `multipart/form-data`, pass each documented binary field as `--multipart-file FIELD=PATH`; repeat the option for array fields. The helper constructs the MIME boundary and body. Do not hand-build multipart bodies or set their `Content-Type`.
   - Never put credentials in a body file or multipart field.
8. Execute only through the request helper. Do not use raw `curl`, HTTP libraries in ad-hoc code, browser JavaScript, Roblox Studio HTTP tools, or shell interpolation of the key.
9. Separate credential presence, authentication, and authorization before giving remediation:
   - Gate `configured: false`: no key reached the agent process. Open the creation page, explain how to set `ROBLOX_OPEN_CLOUD_API_KEY`, and stop.
   - Gate `configured: true` plus HTTP `401`: a key is present but Roblox rejected authentication. Say the environment variable is configured; ask the user to verify the existing key's enabled/status/expiration or regenerate it if invalid. Do not misreport it as missing.
   - Gate `configured: true` plus HTTP `403`: the key is present and the failure is authorization, not environment setup. Report every documented required scope, include the literal API Key management URL `https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab`, and ask the user to edit the existing key's API operations, target experience/resource restrictions, accepted IPs, and status. Do not tell the user to create a key, set the environment variable, restart the agent, or paste/re-enter the key. A bare “Creator Dashboard” mention is insufficient.
   Keep the credential-gate setup instructions out of `401` and `403` responses; mixing those branches makes users troubleshoot the wrong problem.
10. Follow documented asynchronous operations to their terminal status. A side-effect-free `POST` query can require a result/status poll without becoming a mutation.
11. For mutations, perform the documented read-back when one exists and report the observed result separately from the initial response.
12. Remove temporary request/response files containing user data when they are no longer needed. Do not delete user-authored files.

## OpenAPI lookup commands

Search the live official document with the expected effect and distinguishing resource terms:

```bash
python3 scripts/openapi_lookup.py search \
  --query 'list universe data stores' \
  --method GET \
  --required-term 'data store'
```

For saved Creator Store assets, retain the `save` qualifier instead of accepting generic asset search:

```bash
python3 scripts/openapi_lookup.py search \
  --query 'creator store saved assets' \
  --method GET \
  --required-term save
```

Resolve one exact operation and its directly referenced component schemas:

```bash
python3 scripts/openapi_lookup.py operation \
  --method GET \
  --path '/cloud/v2/universes/{universe_id}/data-stores'
```

Follow one nested component only when its fields matter to the request or response:

```bash
python3 scripts/openapi_lookup.py component \
  --reference '#/components/schemas/ListDataStoresResponse'
```

The helper downloads only `https://create.roblox.com/docs/cloud/openapi.json`, refuses redirects away from `create.roblox.com`, and never reads the API-key environment variable. Its compact JSON preserves Roblox extension fields, omits recursively nested schemas until requested, and returns `fallback_required: true` when the exact operation is absent.

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

Multipart upload with a repeated binary field:

```bash
python3 scripts/open_cloud_request.py request \
  --method POST \
  --url 'https://apis.roblox.com/EXACT_DOCUMENTED_PATH' \
  --required-scope 'EXACT_DOCUMENTED_WRITE_SCOPE' \
  --multipart-file 'files=/path/to/thumbnail-1.png' \
  --multipart-file 'files=/path/to/thumbnail-2.png'
```

Save a response without printing its body:

```bash
python3 scripts/open_cloud_request.py request \
  --method GET \
  --url 'https://apis.roblox.com/EXACT_DOCUMENTED_PATH' \
  --required-scope 'EXACT_DOCUMENTED_SCOPE' \
  --output /tmp/roblox-open-cloud-response.json
```

The helper accepts `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`; only `https://apis.roblox.com` is allowed. Repeat `--required-scope` when an operation requires multiple scopes. Use `--data-file` for one raw body or repeat `--multipart-file FIELD=PATH` for documented multipart binary fields; these modes are mutually exclusive, and the helper generates the multipart boundary. The helper reports required scopes and the credential dashboard on `403`. It does not follow redirects because forwarding an authenticated header to a redirected destination can leak a credential.

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
- OpenAPI documentation: <https://create.roblox.com/docs/cloud/reference/openapi>
- Live OpenAPI document: <https://create.roblox.com/docs/cloud/openapi.json>
- Open Cloud overview/reference: <https://create.roblox.com/docs/cloud>
- Credential dashboard: <https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab>

## Result format

Keep the response concise:

Match the user's latest language in both prose and field labels. Before replying, translate every result label; leaving `Credential`, `Request`, or other template labels in English makes an otherwise Japanese response inconsistent. Keep exact scope identifiers, URLs, HTTP tokens, OpenAPI fields, and JSON fields untranslated.

For a Japanese request, use:

```text
認証情報: configured | missing
リクエスト: METHOD https://apis.roblox.com/…
結果: HTTP <status> — <documented meaning>
必要な権限: <exact documented scopes; always include on 403>
仕様根拠: OpenAPI <version and externalDocs> | official reference fallback (OpenAPI operation absent)
検証: <read-back result, not applicable, or not performed>
次の対応: <on 403, edit the existing configured key at literal https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab and check resource/IP/status; never repeat missing-key environment setup>
```

For an English request, use the equivalent labels `Credential`, `Request`, `Result`, `Required permissions`, `Contract source`, `Verification`, and `Next`. For any other language, translate those labels into that language rather than falling back to English.

Before sending a `403` response, scan it for and remove any instruction to create a key, set or re-enter `ROBLOX_OPEN_CLOUD_API_KEY`, or restart/relaunch the agent. Those actions belong only to `configured: false`.

Never include request headers, the key, or a command containing the key.
