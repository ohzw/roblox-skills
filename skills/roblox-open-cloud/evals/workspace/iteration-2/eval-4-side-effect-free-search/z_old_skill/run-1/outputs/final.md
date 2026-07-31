Credential: configured (API key was not exposed)
Request: POST https://apis.roblox.com/toolbox-service/v2/assets:search with query `tree`
Result: HTTP 403 — `Scope not authorized.`
Required scope: `creator-store-product:read`
Verification: The permitted search request was attempted through the old snapshot helper; no mutation occurred.
Next: Grant the API key the exact `creator-store-product:read` scope, then retry the search.
