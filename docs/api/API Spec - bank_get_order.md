---
title: API Spec - bank_get_order
permalink: /api-specs/bank-get-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-08 | `order_status` 對齊 `order.status` 六態（小寫）；發卡主機端不分 status 全回（含 `failed`）；`failed` 訂單 `discount_amount = 0`、`finalized_at = null`；`finalized_at` 說明改為終結（`completed`/`cancelled`）前為 null |
| 2026-06-15 | 從 get_order 拆分而來，僅供發卡主機端使用，回傳 order status 與必要欄位 |

# API: bank_get_order（發卡主機端）

## 功能說明
讓發卡主機依 `order_id` 查詢單筆訂單的當前狀態與折抵金額，供銀行確認訂單是否成立及清算結果。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - API Key 須為發卡主機專屬授權
  - `order_id` 必須存在於神坊系統中

## 使用情境
發卡主機於 `create_order` 或 `finalize_order` 後，依需要查詢訂單當前狀態與實際折抵金額。

# Request
HTTP method: `GET`
Endpoint: `/bank/get_order`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{issuer_api_key}} |

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
  "order_status": "completed",
  "discount_amount": 141,
  "finalized_at": "2026-10-03T10:00:00+08:00",
  "created_at": "2026-10-01T14:30:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| order_status | String | 訂單當前狀態，取自 `order.status` 六態：`pending` \| `processing` \| `waiting_finalization` \| `failed` \| `completed` \| `cancelled`；發卡主機端**不分 status 一律全回**（含清算失敗的 `failed`） |
| discount_amount | Integer | 本次實際折抵總金額（元）；`failed` 訂單為 `0` |
| finalized_at | String \| null | 訂單終結時間；未終結（`pending`/`processing`/`waiting_finalization`/`failed`）時為 `null`，`completed` / `cancelled` 時為終結時間 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `ORDER_NOT_FOUND` | `order_id` 不存在於神坊系統中 |
