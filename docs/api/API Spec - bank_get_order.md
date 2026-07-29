---
title: API Spec - bank_get_order
permalink: /api-specs/bank-get-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-29 | 全系統時間精度盤點：`finalized_at`／`created_at` 補註「毫秒精度」，Sample 補上 `.000` 精度，與其餘系統產生的時間欄位一致 |
| 2026-07-24 | 訂單層級 `discount_amount` 更名為 `total_discount_amount`，與 `create_order`／`get_member_orders` 同步統一命名（「加總」用 `total_discount_amount`、「單張券」維持 `discount_amount`）；`coupons_used[].discount_amount`（單張券金額）不受影響 |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`、`failed` 更名為 `error`；原「`processing`＝清算中」之暫態定義移除，併入 `pending` |
| 2026-07-09 | 新增 `points_used` 與 `coupons_used[]` 對帳明細（與 `create_order` response 同結構），供發卡主機事後重查對帳；舊券（`is_new_issued=false`）本次不扣點故 `tree_points`/`cub_points` 為 0；`failed` 訂單 `coupons_used[]` 為空陣列、`points_used` 皆為 0 |
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
發卡主機於 `create_order` 或 `batch_finalize_orders` 後，依需要查詢訂單當前狀態、實際折抵金額，以及 `coupons_used[]` 對帳明細（含每張券的折抵與 `tree_points`/`cub_points` 點數拆分）。此明細與 `create_order` 建單當下回傳者一致，供發卡主機事後批次對帳重查。

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
  "total_discount_amount": 141,
  "points_used": {
    "tree_points": 8,
    "cub_points": 12
  },
  "coupons_used": [
    {
      "coupon_id": "01HZYA1B2C3D4E5F6G7H8J9K0M",
      "campaign_id": "01HZY7SAYR7J2R4T6W8X1Z3AEH",
      "is_new_issued": false,
      "min_order_amount": 400,
      "discount_amount": 120,
      "redeem_points": 100,
      "tree_points": 0,
      "cub_points": 0,
      "expired_at": "2026-10-31T23:59:59.999+08:00"
    },
    {
      "coupon_id": "01HZYB2C3D4E5F6G7H8J9K0MNP",
      "campaign_id": "01HZY8TBZS8K3S5V7X9Y2A4BFJ",
      "is_new_issued": true,
      "min_order_amount": 100,
      "discount_amount": 21,
      "redeem_points": 20,
      "tree_points": 8,
      "cub_points": 12,
      "expired_at": "2026-11-30T23:59:59.999+08:00"
    }
  ],
  "finalized_at": "2026-10-03T10:00:00.000+08:00",
  "created_at": "2026-10-01T14:30:00.000+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| order_status | String | 訂單當前狀態，取自 `order.status` 五態：`pending` \| `processing` \| `error` \| `completed` \| `cancelled`；發卡主機端**不分 status 一律全回**（含清算失敗的 `error`） |
| total_discount_amount | Integer | 本次實際折抵總金額（元）；`error` 訂單為 `0` |
| points_used | Object | 本次扣點總計（僅新券消耗）；`error` 訂單 `tree_points`/`cub_points` 皆為 `0`，見下表 |
| coupons_used | Array | 本次訂單所用的所有券明細（含舊券與新券），與 `create_order` response 同結構，供發卡主機對帳；`error` 訂單為空陣列，見下表 |
| finalized_at | String \| null | 訂單終結時間（UTC+8 ISO 8601，毫秒精度）；未終結（`pending`/`processing`/`error`）時為 `null`，`completed` / `cancelled` 時為終結時間 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601，毫秒精度） |

### points_used
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| tree_points | Integer | 本次使用的小樹點(生活)總數 |
| cub_points | Integer | 本次使用的小樹點(信用卡)總數 |

### coupons_used
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| coupon_id | String | 券識別碼（ULID） |
| campaign_id | String | 該券所屬 campaign 識別碼（ULID） |
| is_new_issued | Boolean | `true`：本訂單即時發行的新券；`false`：本訂單之前已存在的舊券 |
| min_order_amount | Integer | 該券對應的最低消費門檻（元） |
| discount_amount | Integer | 該券本次實際折抵金額（元） |
| redeem_points | Integer | 該券**發行時**的點數成本（固定屬性，非本次扣點）；新券等於本次 `tree_points + cub_points`，舊券為其原始發行成本 |
| tree_points | Integer | 該券於**本次訂單**消耗的小樹點(生活)；舊券本次不扣點，固定為 `0` |
| cub_points | Integer | 該券於**本次訂單**消耗的小樹點(信用卡)；舊券本次不扣點，固定為 `0` |
| expired_at | String | 該券到期時間（UTC+8 ISO 8601，毫秒精度、含邊界） |

### 對帳恆等式（僅新券貢獻點數）
- `Σ coupons_used[].tree_points == points_used.tree_points`
- `Σ coupons_used[].cub_points == points_used.cub_points`
- `Σ coupons_used[].discount_amount == total_discount_amount`（含舊券與新券）
- `cub_points`（小樹點信用卡）為銀行發行點數，是發卡主機對帳的主要依據；此明細與 `create_order` 建單當下回傳者一致，供事後重查

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `ORDER_NOT_FOUND` | `order_id` 不存在於神坊系統中 |
