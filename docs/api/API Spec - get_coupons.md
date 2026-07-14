---
title: API Spec - get_coupons
permalink: /api-specs/get-coupons/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-14 | 修正說明不清：`id`（券識別碼）型別補上 ULID 註記；sample 的 `CPN_001`/`CPN_002` 佔位字串改為 ULID 格式，避免誤導實際格式 |
| 2026-07-13 | Response 精簡化：`coupons[]` 移除列表畫面不需要的 `brand`、`redeem_points`、`discount_rate`、`max_redemptions_per_order`、`created_at`，`campaign` 巢狀物件改為扁平 `campaign_name`；同時調整同一狀態 bucket 排序規則：`AVAILABLE`/`CONSUMED`/`EXPIRED` 改為 `expired_at DESC`、`id ASC`，`SETTLED` 改依 `updated_at DESC`（finalize 時間）、`id ASC` |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `status` 改為可複選（`status[]`，repeatable query param） |
| 2026-07-02 | `brand_*` 欄位改為巢狀 `brand: {id, name, logo}`；`campaign_*` 欄位改為巢狀 `campaign: {id, name, type}` |
| 2026-07-01 | `brand_id` 限制由 UUID 改為 ULID；`brand_id`/`campaign_id` 範例值改為 ULID 格式 |
| 2026-06-23 | 由 `get_coupon_wallet` 改名為 `get_coupons`；端點更新為 `/coupon/get_coupons` |
| 2026-06-16 | 欄位去除多餘 prefix：`coupon_id` → `id`；coupon 快照欄位 `coupon_min_order_amount/redeem_points/discount_amount` → `min_order_amount/redeem_points/discount_amount`；`PROCESSING/COMPLETED` status 值同步改為 `CONSUMED/SETTLED` |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled`；更新預設排序 bucket 說明 |
| 2026-06-15 | 每張券新增 `campaign_type`（`auto`\|`manual`）與 `discount_rate` 計算欄位 |
| 2026-06-12 | `user_id` → `member_id`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: get_coupons

## 功能說明
讓樹配券平台前台端以 API Key 依 `member_id` 查詢該用戶的券列表，支援依 `brand_id` 與單一 `status` 篩選，供前端呈現特定品牌下的可用券、處理中券與歷史券。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - `brand_id` 若有帶入，必須存在於神坊系統中
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境
前台端由品牌卡片（`get_coupon_wallet`）進入後，帶入 `member_id` 與 `brand_id` 查詢該品牌下的券列表。若前端只想看特定券狀態，可搭配 `status` 進行篩選。

若使用者在該品牌目前沒有任何券，回傳 `coupons: []`，不視為錯誤。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_coupons`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | UUID |
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 20 | > 0 |
| brand_id | string | FALSE | FALSE | ❎ | ULID |
| status[] | string | FALSE | FALSE | ❎ | 可重複帶入，每個值僅接受 `AVAILABLE` \| `CONSUMED` \| `SETTLED` \| `EXPIRED`；不帶表示回傳全部狀態 |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 3,
  "coupons": [
    {
      "id": "01HZYA1B2C3D4E5F6G7H8J9K0M",
      "status": "AVAILABLE",
      "campaign_name": "滿100折21",
      "min_order_amount": 100,
      "discount_amount": 21,
      "expired_at": "2026-10-31T23:59:59.999+08:00"
    },
    {
      "id": "01HZYB2C3D4E5F6G7H8J9K0MNP",
      "status": "CONSUMED",
      "campaign_name": "滿100折21",
      "min_order_amount": 100,
      "discount_amount": 21,
      "expired_at": "2026-10-31T23:59:59.999+08:00"
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
| coupons | Array | 該用戶符合篩選條件的券列表 |

### coupons

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 券識別碼（ULID） |
| status | String | 券狀態：`AVAILABLE` \| `CONSUMED` \| `SETTLED` \| `EXPIRED` |
| campaign_name | String | 該券所屬 campaign 名稱 |
| min_order_amount | Integer | 該券對應的消費門檻金額（元） |
| discount_amount | Integer | 該券折抵金額（元） |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |

### 邏輯說明
- 預設回傳該用戶所有券狀態，不只 `AVAILABLE`
- 若帶 `status[]`，僅回傳指定狀態的券；可同時帶多個值（例如 `?status[]=AVAILABLE&status[]=CONSUMED`）
- 若帶 `brand_id`，僅回傳該品牌底下的券
- 預設排序先依狀態 bucket：`AVAILABLE` → `CONSUMED` → `SETTLED` → `EXPIRED`
- 同一狀態 bucket 內排序：
  - `AVAILABLE`、`CONSUMED` bucket 依 `expired_at DESC`、`id ASC` 排序
  - `SETTLED` bucket 依 `updated_at DESC`（finalize 的時間）、`id ASC` 排序
  - `EXPIRED` bucket 依 `expired_at DESC`、`id ASC` 排序
- 無任何符合條件的券時，回傳 `coupons: []`，不報錯
- 本 API 不回傳訂單關聯欄位，例如 `order_id`
- 本 API 回傳精簡化券資訊，供列表畫面使用；不含 `brand`（已由 `brand_id` 篩選帶入）、`redeem_points`、`discount_rate`、`max_redemptions_per_order`、`created_at`。如需完整詳情請呼叫 `get_coupon_detail`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
3. `brand_id` 不存在：`BRAND_NOT_FOUND`
