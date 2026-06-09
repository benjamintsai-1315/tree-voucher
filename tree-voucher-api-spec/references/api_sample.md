# API: {api_name}
## 功能說明
範例：
讓 client_app 以 API Key 搭配 X-Project-Id、X-Merchant-Provider-Key，取得對應曾經建立的 action_code 資訊，可用於查詢該活動規則（ActionRewardRule）當前的狀態，可用 action_code 作為條件查詢特定單一 action_code 的結果，並且需具備分頁參數過濾。

## 權限需求
範例：
- 認證：Authorization: `ApiKey {{client_app_api_key}} `
- 邊界檢查： 
- `X-Merchant-Provider-Key` 必須為 action_code 所屬的商戶
- `X-Merchant-Provider-Key` 必須是 Client 有授權可存取的

## 使用情境
範例：
如不帶入 action_code 則取得該 merchant 底下所有 action_code 的資訊
- 此情況下需要有分頁機制

如帶入 action _code 則取得指定 action_code 對應的完整規則內容，包含：
- 原始設定資訊（reward、limit、quota...） 
- 累積統計（已發放總點數、剩餘 quota） 
- 狀態資訊（啟用／停用）

# Request 
HTTP method: `GET`
Endpoint: `/client_app/get_action_rules`
Content-Type: `application/json`
## Request Header (表格)
| Header | 說明 |
| ------ | --- |
| Authorization | | ApiKey {{client_app_api_key}} |
| X-Project-Id | {{project_id}} |
| X-Merchant-Provider-Key | {{merchant_provider_key}} |

## Request Parameters

(依照不同 API 請求格式可為 query, json, form)

| 欄位 | 類型 | 必填 | 可空(可省略) | 預設值 | 限制條件 | 
| ---- | ---- | ---- | ---- | ---- | ---- |
| action_code | string | FALSE | FALSE | ❎ | 最多 30 字，僅限英數字 | 
| page | integer | FALSE | FALSE | 1 | > 0 | 
| limit | integer | FALSE | FALSE | 100 | > 0 | 

# Response
## Sample (JSON)
```json

//指定 action_code
{
  "page": 1,
  "limit": 1,
  "total": 1,
  "items": [
    {
      "action_name": "登入會員送 50 點",
      "action_code": "RC_LOGIN50",
      "reward": 50, //一個RC可兌換50點
      "limit": 100,
      "quota": 100000,
      "expire_duration": 90,
      "type": "Redemption",
      "status": "ACTIVE",
      "granted_counts": 150,
      "total_granted_points": 7500,
      "quota_remaining": 92500,
      "created_at": "2026-10-01T12:00:00+08:00",
      "updated_at": "2026-10-08T10:10:00+08:00"
    }
  ]
}

//全部取得
{
  "page": 1,
  "limit": 2,
  "total": 10,
  "items": [
    {
      "action_name": "登入會員送 50 點",
      "action_code": "RC_LOGIN50",
      "reward": 50,
      "limit": 100,
      "quota": 100000,
      "expire_duration": 90,
      "type": "Redemption",
      "status": "ACTIVE",
      "granted_counts": 150,
      "total_granted_points": 7500,
      "quota_remaining": 92500,
      "created_at": "2026-10-01T12:00:00+08:00",
      "updated_at": "2026-10-08T10:10:00+08:00"
    },
    {
      "action_name": "登入會員送 50 點",
      "action_code": "RC_LOGIN50",
      "reward": 50,
      "limit": 100,
      "quota": 100000,
      "expire_duration": 90,
      "type": "Redemption",
      "status": "INACTIVE",
      "granted_counts": 150,
      "total_granted_points": 7500,
      "quota_remaining": 92500,
      "created_at": "2026-10-01T12:00:00+08:00",
      "updated_at": "2026-10-08T10:10:00+08:00"
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 | 
| ---- | ---- | ---- |
| page | Integer | 當前頁碼，從 1 開始 |
| limit | Integer | 每頁筆數 |
| total | Integer | 符合條件的總筆數 |
| items | Array | 符合條件的活動規則列表 |

### items

| 欄位 | 類型 | 說明 | 
| ---- | ---- | ---- |
| action_name | String | 原始設定的活動名稱 | 
| action_code | String | 活動代碼 | 
| reward | Integer | 每份獎勵對應點數，或為一份兌換碼可兌換點數 | 
| limit | Integer | 單一會員累計可獲得的最高份數上限 | 
| quota | Integer | 該檔活動可發送點數之總上限，活動總預算，單位為點數 | 
| expire_duration | Integer | 獎勵點數生效後的有效期，單位為天 | 
| type | String | Redemption | Action ：兌換碼或活動直接給點 | 
| status | String | ACTIVE | INACTIVE：活動狀態是否仍為啟用中可使用 | 
| granted_counts | Integer | 已發送之份數，等同 total_granted_points/reward ，單位為份數 | 
| total_granted_points | Integer | 已發送之點數，單位為點數 | 
| quota_remaining | Integer | 仍可發送之活動點數餘額，等同 quota - total_granted_points，單位為點數 | 
| created_at | String | 活動建立之時間 (系統 UTC8 時間轉字串) | 
| updated_at | String | 活動更新之時間 (系統 UTC8 時間轉字串) | 

### 邏輯說明
- granted_counts 與 total_granted_points 可由 action_transaction 聚合統計，不論 valid_from 的時間是否已到。  
- quota_remaining = quota - total_granted_points，使用上可透過 quota_remaining/reward 判斷剩下可發的份數為多少。
- 若規則 status = "INACTIVE"，仍可查但不可發點。
- 排列順序以 created_at 由新到舊排序

## 400 錯誤回傳（TYPE: MESSAGE）
1. 商戶已停用：`INACTIVE_MERCHANT`
2. 發點代碼不存在：`ACTION_CODE_NOT_FOUND`
