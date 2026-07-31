Credential: configured
Request: GET https://apis.roblox.com/toolbox-service/v1/saves?limit=1&page=1
Result: HTTP 403 — 権限不足（Scope not authorized.）。保存済み Creator Store asset の読み取り結果は取得できませんでした。
Required permissions: creator-store-save:read
Verification: 読み取りは許可された GET を1回だけ実行しました。変更操作（POST/PUT/PATCH/DELETE）は実行していません。
Next: API Key 管理ページ https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab で、次を確認・修正してください。
- API system と operations に `creator-store-save:read` が選択されていること
- 対象 experience または resource の制限が、この保存済み Creator Store asset を許可していること
- 呼び出し元 IP が accepted IP addresses に含まれていること
- API key の status と expiration が有効であること
API key 自体の提示・共有は不要です。権限設定を変更した後、同じ GET を再実行してください。変更は一切行っていません。
