Credential: missing（`ROBLOX_OPEN_CLOUD_API_KEY` は未設定）
Request: 実行しない（APIキーの値や先頭・末尾文字の表示、および `api-keys/v1/introspect` の呼び出しは安全上行えません）
Result: HTTP status なし — 資格情報ゲートで停止しました。実行結果は `configured: false` で、認証情報ページが開かれました。
Verification: 未実施（キー未設定のため）
Next: Creator Dashboard（https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab）で最小権限・適切なリソース制限・有効期限のAPIキーを作成し、`ROBLOX_OPEN_CLOUD_API_KEY` としてエージェント起動時の環境に設定してください。キーをチャット、コマンド引数、ソースコード、リポジトリ、読み取り可能なファイルへ貼り付けないでください。設定後はエージェントを再起動または再起動相当で起動環境を更新してください。