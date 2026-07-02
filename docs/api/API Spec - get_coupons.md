---
title: API Spec - get_coupons
permalink: /api-specs/get-coupons/
---

## Changelog

| Date | Summary |
| ---- | ------- |
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
讓樹享券平台前台端以 API Key 依 `member_id` 查詢該用戶的券列表，支援依 `brand_id` 與單一 `status` 篩選，供前端呈現特定品牌下的可用券、處理中券與歷史券。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - `brand_id` 若有帶入，必須存在於神坊系統中

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
      "id": "CPN_001",
      "status": "AVAILABLE",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店",
        "logo": "https://cdn.example.com/logos/familymart.png"
      },
      "campaign": {
        "id": "01HZY5Q8WP5G7N9R2T4V6X8ZBD",
        "name": "滿100折21",
        "type": "auto"
      },
      "min_order_amount": 100,
      "redeem_points": 20,
      "discount_amount": 21,
      "discount_rate": 1.05,
      "max_redemptions_per_order": 3,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "created_at": "2026-10-01T09:00:00+08:00"
    },
    {
      "id": "CPN_002",
      "status": "CONSUMED",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店",
        "logo": "https://cdn.example.com/logos/familymart.png"
      },
      "campaign": {
        "id": "01HZY5Q8WP5G7N9R2T4V6X8ZBD",
        "name": "滿100折21",
        "type": "auto"
      },
      "min_order_amount": 100,
      "redeem_points": 20,
      "discount_amount": 21,
      "discount_rate": 1.05,
      "max_redemptions_per_order": 3,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "created_at": "2026-10-03T10:30:00+08:00"
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
| id | String | 券識別碼 |
| status | String | 券狀態：`AVAILABLE` \| `CONSUMED` \| `SETTLED` \| `EXPIRED` |
| brand | Object | 對應品牌資訊，見下表 |
| campaign | Object | 該券所屬 campaign 資訊，見下表 |
| min_order_amount | Integer | 該券對應的消費門檻金額（元） |
| redeem_points | Integer | 該券建立時所對應的點數成本 |
| discount_amount | Integer | 該券折抵金額（元） |
| discount_rate | Float | 每點折抵金額比率，`round(discount_amount / redeem_points, 2)`，純計算欄位 |
| max_redemptions_per_order | Integer | 該券所屬 campaign 定義的單筆交易 active campaign 券使用張數上限 |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| created_at | String | 該券建立時間（UTC+8 ISO 8601） |

### brand

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼（ULID） |
| name | String | 品牌名稱 |
| logo | String | 品牌 logo 圖片 URL |

### campaign

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | Campaign 識別碼（ULID） |
| name | String | Campaign 名稱 |
| type | String | Campaign 類型：`auto`（系統自動兌換）\| `manual`（用戶手動兌換） |

### 邏輯說明
- 預設回傳該用戶所有券狀態，不只 `AVAILABLE`
- 若帶 `status[]`，僅回傳指定狀態的券；可同時帶多個值（例如 `?status[]=AVAILABLE&status[]=CONSUMED`）
- 若帶 `brand_id`，僅回傳該品牌底下的券
- 預設排序先依狀態 bucket：`AVAILABLE` → `CONSUMED` → `SETTLED` → `EXPIRED`
- 同一狀態 bucket 內依 `expired_at ASC`、`created_at ASC`、`id ASC` 排序
- 無任何符合條件的券時，回傳 `coupons: []`，不報錯
- 本 API 不回傳訂單關聯欄位，例如 `order_id`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `brand_id` 不存在：`BRAND_NOT_FOUND`
