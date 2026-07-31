社内メモの `POST` は誤りです。

公式仕様の「List Data Stores」は、次の読み取り専用リクエストです。

- **method**: `GET`
- **URL**: `https://apis.roblox.com/cloud/v2/universes/987654321/data-stores`
- **必要なスコープ**: `universe-datastores.control:list`

したがって、Data Store一覧の取得に `POST` を使うべきではありません。`POST` はこの一覧操作ではなく、Data Storeエントリの作成など別の操作に使われます。公式仕様で確認しただけであり、副作用を避けるためAPIリクエストは実行していません。