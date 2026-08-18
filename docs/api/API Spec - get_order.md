---
title: API Spec - get_order（發卡主機端）
permalink: /api-specs/get-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-18 | `order_status` 新增可回傳值 `revoked`：資料層仍為 `order.status=cancelled` + `cancel_reason=revoked`（銀行送 `batch_finalize_orders action=revoke` 所致），本 API 將此組合對外呈現為 `revoked`，供發卡主機/財務辨識「銀行未確認扣款之撤銷」；一般退刷（`cancel_reason=cancel`）維持 `cancelled`。`revoked` 之 `total_discount_amount=0`、`finalized_at` 為終結時間，與 `cancelled` 一致 |
| 2026-08-06 | API 更名 `bank_get_order` → `get_order`：路徑本身已含 `/bank/` 前綴，與其他 `/bank/...` API（`create_order`、`batch_finalize_orders`、`get_finalize_batch_status`）一致採「動詞_目標對象」命名結構，不再另加 `bank_` 前綴；原前台端 `get_order`（已於 2026-07-08 廢除）之 spec 文件移至 `docs/api/legacy/`，讓出此名稱 |
| 2026-08-06 | Response 結構改為與 `create_order` 對齊：移除逐張 `coupons_used[]`／`points_used` 明細，改用 `coupon_summary`（`new_issued`／`existing` 彙總，與 `create_order` response 同結構）；保留 `order_id`（回顯查詢參數）與 `finalized_at`（`create_order` 建單當下尚無終結時間，故該 API 不含此欄位） |
| 2026-07-29 | 全系統時間精度盤點：`finalized_at`／`created_at` 補註「毫秒精度」，Sample 補上 `.000` 精度，與其餘系統產生的時間欄位一致 |
| 2026-07-24 | 訂單層級 `discount_amount` 更名為 `total_discount_amount`，與 `create_order`／`get_member_orders` 同步統一命名（「加總」用 `total_discount_amount`、「單張券」維持 `discount_amount`）；`coupons_used[].discount_amount`（單張券金額）不受影響 |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`、`failed` 更名為 `error`；原「`processing`＝清算中」之暫態定義移除，併入 `pending` |
| 2026-07-09 | 新增 `points_used` 與 `coupons_used[]` 對帳明細（與 `create_order` response 同結構），供發卡主機事後重查對帳；舊券（`is_new_issued=false`）本次不扣點故 `tree_points`/`cub_points` 為 0；`failed` 訂單 `coupons_used[]` 為空陣列、`points_used` 皆為 0 |
| 2026-07-08 | `order_status` 對齊 `order.status` 六態（小寫）；發卡主機端不分 status 全回（含 `failed`）；`failed` 訂單 `discount_amount = 0`、`finalized_at = null`；`finalized_at` 說明改為終結（`completed`/`cancelled`）前為 null |
| 2026-06-15 | 從 get_order 拆分而來，僅供發卡主機端使用，回傳 order status 與必要欄位 |

# API: get_order（發卡主機端）

## 功能說明
讓發卡主機依 `order_id` 查詢單筆訂單的當前狀態與折抵金額，供銀行確認訂單是否成立及清算結果。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - API Key 須為發卡主機專屬授權
  - `order_id` 必須存在於神坊系統中

## 使用情境
發卡主機於 `create_order` 或 `batch_finalize_orders` 後，依需要查詢訂單當前狀態、實際折抵金額，以及 `coupon_summary` 對帳彙總（依新發券／既有券分組，各含折抵金額與 `tree_points`/`cub_points` 點數拆分）。此彙總與 `create_order` 建單當下回傳者同結構，供發卡主機事後批次對帳重查。

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
  "total_discount_amount": 109,
  "created_at": "2026-10-01T14:30:00.000+08:00",
  "coupon_summary": {
    "new_issued": { "quantity": 2, "total_discount_amount": 46, "tree_points": 30, "cub_points": 10 },
    "existing": { "quantity": 3, "total_discount_amount": 63, "tree_points": 25, "cub_points": 38 }
  },
  "finalized_at": "2026-10-03T10:00:00.000+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| order_status | String | 訂單當前狀態：`pending` \| `processing` \| `error` \| `completed` \| `cancelled` \| `revoked`；發卡主機端**不分 status 一律全回**（含清算失敗的 `error`）。前五者直接取自 `order.status`（資料層仍為五態）；`revoked` 為**呈現層衍生值**——資料層 `order.status` 仍為 `cancelled`，當其 `cancel_reason=revoked`（銀行 `action=revoke` 撤銷、非真實退刷）時本 API 回傳 `revoked`，以與一般退刷（`cancel_reason=cancel` → `cancelled`）區分 |
| total_discount_amount | Integer | 本次實際折抵總金額（元），與 `create_order` response 定義相同；`error` 訂單為 `0`；`cancelled`／`revoked` 訂單折抵已取消，亦為 `0` |
| created_at | String | 該筆 order 於神坊資料庫中建立的時間（UTC+8 ISO 8601，毫秒精度），與 `create_order` response 定義相同 |
| coupon_summary | Object | 本次折抵金額與點數消耗，依新發券／既有券分組彙總，與 `create_order` response 同結構，供發卡主機對帳；`error` 訂單兩分組皆為 `0`，見下表 |
| finalized_at | String \| null | 訂單終結時間（UTC+8 ISO 8601，毫秒精度）；未終結（`pending`/`processing`/`error`）時為 `null`，`completed` / `cancelled` / `revoked` 時為終結時間 |

### coupon_summary

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| new_issued | Object | 本次訂單**新券段**即時發行之新券的彙總，見下表 |
| existing | Object | 本次訂單**既有券段**使用之舊券的彙總，見下表 |

`new_issued` 與 `existing` 皆為同一結構：

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| quantity | Integer | 該分組使用的券張數 |
| total_discount_amount | Integer | 該分組本次折抵金額合計（元） |
| tree_points | Integer | `new_issued`：本次訂單消耗的小樹點(生活)總數；`existing`：該分組舊券於其**原始發行時**所使用的小樹點(生活)總數（非本次消耗，僅呈現歷史組成） |
| cub_points | Integer | `new_issued`：本次訂單消耗的小樹點(信用卡)總數；`existing`：該分組舊券於其**原始發行時**所使用的小樹點(信用卡)總數（原因同上） |

### 對帳恆等式
- `coupon_summary.new_issued.total_discount_amount + coupon_summary.existing.total_discount_amount == total_discount_amount`
- `cub_points`（小樹點信用卡）為銀行發行點數，是發卡主機對帳的主要依據；此彙總與 `create_order` 建單當下回傳者同結構，供事後重查

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `ORDER_NOT_FOUND` | `order_id` 不存在於神坊系統中 |
