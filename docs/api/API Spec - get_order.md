---
title: API Spec - get_order
permalink: /api-specs/get-order/
---

> **⚠️ Deprecated：** 前台端已不再提供單筆訂單明細查詢。訂單摘要列表請用 [`get_member_orders`](API%20Spec%20-%20get_member_orders.md)；發卡主機端單筆訂單狀態查詢由 [`bank_get_order`](API%20Spec%20-%20bank_get_order.md) 取代。請勿使用本文件。

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-08 | **Deprecated**：前台端單筆明細查詢廢除（前台不需單筆明細），發卡主機端由 `bank_get_order` 取代 |
| 2026-07-08 | `order_status` 對齊 `order.status` 六態（小寫），前台端剔除 `failed`（改回 `ORDER_NOT_FOUND`）；actions 映射更新 `CREATED` → `waiting_finalization`；`finalize_order` 敘述改為 `batch_finalize_orders` |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-06-16 | `coupons_used[]` 欄位去除多餘 prefix：`coupon_id` → `id`；`coupon_min_order_amount/redeem_points/discount_amount` → `min_order_amount/redeem_points/discount_amount` |
| 2026-07-01 | `brand_id`/`campaign_id` 範例值改為 ULID 格式，並於 response items 補上 ULID 型別註記 |
| 2026-06-15 | `coupons_used[]` 新增 `discount_rate` 計算欄位 |
| 2026-06-15 | 拆分為前台端（`/coupon/get_order`）與發卡主機端（`/bank/get_order`）兩支獨立 API；前台端加入 `member_id` 參數防呆，回傳完整訂單與事件歷程；發卡主機端請見 [API Spec - bank_get_order](API Spec - bank_get_order.md) |
| 2026-06-15 | 路徑依呼叫端拆分（原共用同一份 spec） |
| 2026-06-12 | response 欄位 `user_id` → `member_id` |

# API: get_order（前台端）

## 功能說明
讓樹配券平台前台端依 `order_id` 與 `member_id` 查詢單筆訂單的完整資訊，包含折抵券明細與從建立到結單的事件歷程。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權
  - `order_id` 必須存在於神坊系統中
  - `order_id` 對應訂單的 `member_id` 必須與 request 帶入的 `member_id` 相符，否則回 `ORDER_NOT_FOUND`
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境
前台端帶入 `order_id` 與 `member_id` 查詢該筆訂單的當前狀態、折抵明細及事件歷程，供用戶於歷史紀錄頁面查看。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_order`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| order_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| member_id | string | TRUE | FALSE | ❎ | 最多 36 字 |

# Response
## Sample（JSON）

```json
{
  "order_id": "ORD_20261001_00001",
  "member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683",
  "brand_id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
  "brand_name": "全家便利商店",
  "cash_amount": 620,
  "card_last_four_digits": "1234",
  "discount_amount": 141,
  "order_status": "completed",
  "finalized_at": "2026-10-03T10:00:00+08:00",
  "coupons_used": [
    {
      "id": "CPN_001",
      "campaign_id": "01HZY7SAYR7J2R4T6W8X1Z3AEH",
      "min_order_amount": 400,
      "redeem_points": 100,
      "discount_amount": 120,
      "discount_rate": 1.2,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "type": "EXISTING"
    },
    {
      "id": "CPN_002",
      "campaign_id": "01HZY8TBZS8K3S5V7X9Y2A4BFJ",
      "min_order_amount": 100,
      "redeem_points": 20,
      "discount_amount": 21,
      "discount_rate": 1.05,
      "expired_at": "2026-11-30T23:59:59.999+08:00",
      "type": "NEWLY_ISSUED"
    }
  ],
  "actions": [
    {
      "action": "CREATED",
      "created_at": "2026-10-01T14:30:00+08:00"
    },
    {
      "action": "COMPLETED",
      "created_at": "2026-10-03T10:00:00+08:00"
    }
  ],
  "created_at": "2026-10-01T14:30:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| member_id | String | 神坊會員識別碼 |
| brand_id | String | 對應 brand 識別碼（ULID） |
| brand_name | String | 對應 brand 名稱 |
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| discount_amount | Integer | 本次實際折抵總金額（元） |
| order_status | String | 訂單當前狀態，取自 `order.status` 六態；本前台端與 `get_member_orders` 一致**剔除 `failed`**，實際僅出現 `waiting_finalization` \| `completed` \| `cancelled` |
| finalized_at | String \| null | 訂單終結時間；未終結（`waiting_finalization`）時為 `null`，`completed` / `cancelled` 時為終結時間 |
| coupons_used | Array | 本次被使用的券明細 |
| actions | Array | 訂單事件歷程，依發生時間由舊到新排列 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

### coupons_used

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 券識別碼 |
| campaign_id | String | 該券所屬 campaign 識別碼（ULID） |
| min_order_amount | Integer | 該券對應的消費門檻金額（元） |
| redeem_points | Integer | 該券建立時所對應的點數成本 |
| discount_amount | Integer | 該券的折抵金額（元） |
| discount_rate | Float | 每點折抵金額比率，`round(discount_amount / redeem_points, 2)`，純計算欄位 |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| type | String | `EXISTING`：原券夾既有券；`NEWLY_ISSUED`：本次即時兌換產生 |

### actions

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| action | String | 事件類型：`CREATED` \| `COMPLETED` \| `CANCELLED` |
| created_at | String | 事件發生時間（UTC+8 ISO 8601） |

### 邏輯說明
- `discount_amount` = Σ `coupons_used[].discount_amount`
- `coupons_used[]` 對應 DB layer 的 `order_coupon_logs`
- `actions` 對應 DB layer 的 `order_logs`
- `actions` 最少一筆（`CREATED`），`batch_finalize_orders` 執行後新增第二筆（`COMPLETED` 或 `CANCELLED`）
- `order_status`（`order.status` 六態）與 `actions` 最後一筆的 `action` 對應：`CREATED` → `waiting_finalization`、`COMPLETED` → `completed`、`CANCELLED` → `cancelled`（清算中的 `pending` / `processing` 為暫態、不會有對應 action；`failed` 訂單不由本前台端回傳）
- `member_id` 不符、或訂單為 `failed`（清算失敗）時，一律回 `ORDER_NOT_FOUND`，不透露訂單存在與否
- `card_last_four_digits` 為建單時由發卡主機提供並保存於訂單上的顯示資訊，不參與任何清算邏輯

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `ORDER_NOT_FOUND` | `order_id` 不存在、`member_id` 與訂單不符，或訂單為 `failed`（清算失敗、不對前台端揭露） |
