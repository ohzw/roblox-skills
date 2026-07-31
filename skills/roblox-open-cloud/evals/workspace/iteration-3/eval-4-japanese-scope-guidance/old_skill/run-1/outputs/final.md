Credential: configured
Request: POST https://apis.roblox.com/toolbox-service/v2/assets:search
Result: HTTP 400 — `Either searchCategoryType or categoryPath must be provided.`。認証は成功しましたが、指定された本文 `{ "query": "tree" }` だけでは検索APIの入力要件を満たさないため、検索結果は返りませんでした。
Required permissions: `creator-store-product:read`
Verification: 検索のみを実行しました。リソースの作成・更新・削除などの変更は行っていません。
Next: 権限不足（HTTP 403）ではありません。追加のscopeは不要です。API仕様上必要な `searchCategoryType` または `categoryPath` を含む、ユーザーが明示的に許可した検索条件が必要です。
