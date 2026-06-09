# API: {api_name}
## 功能說明
讓 {caller} 以 API Key 搭配 {headers}，{動作描述}。

## 權限需求
- 認證：Authorization: `ApiKey {{client_app_api_key}}`
- 邊界檢查：
  - `{header}` 必須為 {resource} 所屬的 {owner}
  - `{header}` 必須是 Client 有授權可存取的

## 使用情境
{情境一描述}
{情境二描述（如有）}

# Request
HTTP method: `{GET|POST|PUT|DELETE|PATCH}`
Endpoint: `/{namespace}/{api_name}`
Content-Type: `application/json`

## Request Header（表格）
| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{client_app_api_key}} |
| X-Project-Id | {{project_id}} |
| X-Merchant-Provider-Key | {{merchant_provider_key}} |

## Request Parameters
（query / json / form）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| {field} | string | FALSE | FALSE | ❎ | 最多 30 字，僅限英數字 |
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 100 | > 0 |

# Response
## Sample（JSON）
```json
{
  "page": 1,
  "limit": 1,
  "total": 1,
  "items": [
    {
      "field_name": "value" // 說明
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
| items | Array | 回傳資料列表 |

### items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| field_name | String | 說明 |
| created_at | String | 建立時間（系統 UTC+8 時間轉字串） |
| updated_at | String | 更新時間（系統 UTC+8 時間轉字串） |

### 邏輯說明
- {計算欄位} = {公式}
- 排列順序以 created_at 由新到舊排序

## 400 錯誤回傳（TYPE: MESSAGE）
1. 商戶已停用：`INACTIVE_MERCHANT`
2. 資源不存在：`{RESOURCE}_NOT_FOUND`
