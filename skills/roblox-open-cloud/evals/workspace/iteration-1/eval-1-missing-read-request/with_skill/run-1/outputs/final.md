Credential: missing
Request: GET https://apis.roblox.com/…（Data Store一覧の取得）
Result: APIキーが未設定（`ROBLOX_OPEN_CLOUD_API_KEY` が空）だったため、リクエストは実行していません。
Verification: 未実施（認証情報のゲートで停止）
Next: Roblox Creator Dashboard の [API Keys](https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab) で、対象の universe 987654321 に必要な最小権限だけを持つキーを作成し、エージェント起動時の環境に `ROBLOX_OPEN_CLOUD_API_KEY` として設定してください。キーをチャット、コマンド引数、ソースコード、リポジトリ、またはエージェントが読めるファイルに貼り付けないでください。設定後、エージェントを再起動して再実行してください。