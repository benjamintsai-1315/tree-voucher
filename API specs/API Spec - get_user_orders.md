---
title: API Spec - get_user_orders
permalink: /api-specs/get-user-orders/
---

# API: get_user_orders

## 功能說明
讓樹享券平台前台端以 API Key 依 user_id 取得該用戶的訂單列表，支援分頁與排序，供用戶瀏覽歷史折抵紀錄。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受發卡主機的 API Key
  - `user_id` 必須存在於神坊系統中

## 使用情境
前台端帶入 `user_id` 取得該用戶所有訂單的摘要列表；如需查看單筆完整明細（含 events 歷程），再以 `order_id` 呼叫 `get_order`。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_user_orders`
Content-Type: `application/json`

## Request Header（表格）
| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| user_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 20 | > 0 |
| sort_by | string | FALSE | FALSE | `created_at` | 僅接受 `created_at` \| `order_status` |
| sort_order | string | FALSE | FALSE | `DESC` | 僅接受 `ASC` \| `DESC` |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 3,
  "items": [
    {
      "order_id": "ORD_20261001_00001",
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "cash_amount": 620,
      "card_last_four_digits": "1234",
      "discount_amount": 141,
      "order_status": "COMPLETED",
      "finalized_at": "2026-10-03T10:00:00+08:00",
      "created_at": "2026-10-01T14:30:00+08:00"
    },
    {
      "order_id": "ORD_20261002_00005",
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "cash_amount": 300,
      "card_last_four_digits": "5678",
      "discount_amount": 21,
      "order_status": "PROCESSING",
      "finalized_at": null,
      "created_at": "2026-10-02T09:10:00+08:00"
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
| items | Array | 訂單摘要列表 |

### items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| brand_id | String | 對應 brand 識別碼 |
| brand_name | String | 對應 brand 名稱 |
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| discount_amount | Integer | 本次實際折抵總金額（元） |
| order_status | String | 訂單當前狀態：`PROCESSING` \| `COMPLETED` \| `CANCELLED` |
| finalized_at | String \| null | 訂單最終化時間；`PROCESSING` 時為 `null` |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

### 邏輯說明
- 列表為摘要資訊，不含 `coupons_used` 明細與 `events` 歷程；完整資訊請呼叫 `get_order`
- `items` 內的 `card_last_four_digits` 為建單時由發卡主機提供，供前台端在訂單列表顯示卡號辨識資訊
- `sort_by = created_at`：依訂單建立時間排序
- `sort_by = order_status`：依狀態排序，順序為 `PROCESSING` → `COMPLETED` → `CANCELLED`

## 400 錯誤回傳（TYPE: MESSAGE）
1. API Key 非前台端授權：`CALLER_NOT_AUTHORIZED`
2. user_id 不存在：`USER_NOT_FOUND`
