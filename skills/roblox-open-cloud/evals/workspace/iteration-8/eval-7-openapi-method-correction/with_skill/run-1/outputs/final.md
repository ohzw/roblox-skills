認証情報: configured（存在確認のみ実施。APIキーの値は取得・表示していません）
リクエスト: 実行していません（API呼び出し禁止のため）

結論:
社内メモの `POST https://apis.roblox.com/cloud/v2/universes/987654321/data-stores` は、Data Store一覧取得の公式仕様とは一致しません。公式に定義された一覧操作は次のとおりです。

- method: `GET`
- URL: `https://apis.roblox.com/cloud/v2/universes/987654321/data-stores`
- operation: `Cloud_ListDataStores`（`List Data Stores`）
- 必須スコープ: `universe-datastores.control:list`
- リクエストボディ: なし
- `universe_id`: パスパラメーター（必須）

したがって、一覧を読むだけなら `GET` を使います。`POST` はこのコレクションの「Data Store一覧」操作としてOpenAPIに定義されていないため、社内メモのまま送信すべきではありません。今回の検証では副作用を避けるため、POSTはもちろんGETも含めてRoblox APIを一切実行していません。

任意のクエリーパラメーターとして `maxPageSize`（最大100）、`pageToken`、`filter`、`showDeleted` が定義されています。ページング時は、返された `nextPageToken` を次の `pageToken` に使います。デフォルトでは完全削除予定のData Storeは結果から除外されます。

仕様根拠: Roblox公式ライブOpenAPI `https://create.roblox.com/docs/cloud/openapi.json`（OpenAPI `3.0.4`、拡張バージョン `1.1.0`）の `GET /cloud/v2/universes/{universe_id}/data-stores`。公式操作リファレンス: `https://create.roblox.com/docs/cloud/reference/features/storage#Cloud_ListDataStores`
検証: OpenAPI検索および対象operationの解決のみ。APIリクエスト、変更、読み取り実行は未実施。
