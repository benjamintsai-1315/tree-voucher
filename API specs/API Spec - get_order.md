---
title: API Spec - get_order
permalink: /api-specs/get-order/
---

# API: get_order

## 功能說明
讓樹享券平台前台端或發卡主機以 API Key 依 order_id 查詢單筆訂單的完整資訊，包含折抵明細與從建立到結單的事件歷程。DB layer 對應 `order_logs` 與 `order_coupon_items`；API layer 則維持 `events` 與 `coupons_used` 的回傳欄位名稱。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}` 或 `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端或發卡主機授權，其餘一律拒絕
  - `order_id` 必須存在於神坊系統中

## 使用情境
前台端或發卡主機帶入 `order_id` 查詢該筆訂單的當前狀態、折抵明細及事件歷程。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_order`
Content-Type: `application/json`

## Request Header（表格）
| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} 或 ApiKey {{issuer_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| order_id | string | TRUE | FALSE | ❎ | 最多 64 字 |

# Response
## Sample（JSON）

```json
{
  "order_id": "ORD_20261001_00001",
  "user_id": "USR_000123",
  "brand_id": "BRAND_FAMILYMART",
  "brand_name": "全家便利商店",
  "cash_amount": 620,
  "card_last_four_digits": "1234",
  "discount_amount": 141,
  "order_status": "COMPLETED",
  "finalized_at": "2026-10-03T10:00:00+08:00",
  "coupons_used": [
    {
      "coupon_id": "CPN_001",
      "campaign_id": "old_campaign",
      "unit_cash_amount": 400,
      "unit_point_amount": 100,
      "unit_discount_amount": 120,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "type": "EXISTING"
    },
    {
      "coupon_id": "CPN_002",
      "campaign_id": "new_campaign",
      "unit_cash_amount": 100,
      "unit_point_amount": 20,
      "unit_discount_amount": 21,
      "expired_at": "2026-11-30T23:59:59.999+08:00",
      "type": "NEWLY_ISSUED"
    }
  ],
  "events": [
    {
      "event": "CREATED",
      "occurred_at": "2026-10-01T14:30:00+08:00"
    },
    {
      "event": "COMPLETED",        // 或 CANCELLED
      "occurred_at": "2026-10-03T10:00:00+08:00"
    }
  ],
  "created_at": "2026-10-01T14:30:00+08:00"
}
```

## Response items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| user_id | String | 神坊用戶識別碼 |
| brand_id | String | 對應 brand 識別碼 |
| brand_name | String | 對應 brand 名稱 |
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| discount_amount | Integer | 本次實際折抵總金額（元） |
| order_status | String | 訂單當前狀態：`PROCESSING` \| `COMPLETED` \| `CANCELLED` |
| finalized_at | String \| null | 訂單最終化時間；`PROCESSING` 時為 `null` |
| coupons_used | Array | 本次被使用的券明細 |
| events | Array | 訂單事件歷程，依發生時間由舊到新排列 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

### coupons_used
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| coupon_id | String | 券識別碼 |
| campaign_id | String | 該券所屬 campaign 識別碼 |
| unit_cash_amount | Integer | 該券對應的消費門檻金額（元） |
| unit_point_amount | Integer | 該券建立時所對應的點數成本 |
| unit_discount_amount | Integer | 該券的折抵金額（元） |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| type | String | `EXISTING`：原券夾既有券；`NEWLY_ISSUED`：本次即時兌換產生 |

### events
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| event | String | 事件類型：`CREATED` \| `COMPLETED` \| `CANCELLED` |
| occurred_at | String | 事件發生時間（UTC+8 ISO 8601） |

### 邏輯說明
- `discount_amount` = Σ `coupons_used[].unit_discount_amount`
- `coupons_used[]` 對應 DB layer 的 `order_coupon_items`
- `events` 對應 DB layer 的 `order_logs`
- `events` 最少一筆（`CREATED`），finalize_order 執行後新增第二筆（`COMPLETED` 或 `CANCELLED`）
- `order_status` 與 `events` 最後一筆的 `event` 對應：`CREATED` → `PROCESSING`、`COMPLETED` → `COMPLETED`、`CANCELLED` → `CANCELLED`
- `coupons_used[]` 用於還原已使用券的清算結果與有效期，不保證回傳未被使用券清單
- `card_last_four_digits` 為建單時由發卡主機提供並保存於訂單上的顯示資訊，不參與任何清算邏輯
- 重複 `create_order` 或重複 `finalize_order` 不新增第二筆同類事件；重送請求僅回 business error，不產生任何 side effect

## 400 錯誤回傳（TYPE: MESSAGE）
1. API Key 非前台端或發卡主機授權：`CALLER_NOT_AUTHORIZED`
2. order_id 不存在：`ORDER_NOT_FOUND`
