---
title: API Spec - get_coupon_detail
permalink: /api-specs/get-coupon-detail/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-23 | 初版 |

# API: get_coupon_detail

## 功能說明
查詢單張券的完整詳情，包含狀態、效期、折抵規則，以及當初兌換此券所花費的點數。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - `coupon_id` 必須存在且屬於該 `member_id`

## 使用情境
前台端由券列表（`get_coupons`）點入單張券後，顯示該券的完整詳情。`redeem_points` 即為當初兌換此券所花費的點數（coupon 建立時的快照）。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_coupon_detail`
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
| coupon_id | string | TRUE | FALSE | ❎ | ULID |

# Response
## Sample（JSON）

```json
{
  "id": "CPN_001",
  "status": "AVAILABLE",
  "brand_id": "BRAND_FAMILYMART",
  "brand_name": "全家便利商店",
  "brand_logo": "https://cdn.example.com/logos/familymart.png",
  "campaign_id": "CPN_CAMP_001",
  "campaign_name": "滿100折21",
  "campaign_type": "auto",
  "min_order_amount": 100,
  "redeem_points": 20,
  "discount_amount": 21,
  "discount_rate": 1.05,
  "max_redemptions_per_order": 3,
  "expired_at": "2026-10-31T23:59:59.999+08:00",
  "created_at": "2026-10-01T09:00:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 券識別碼 |
| status | String | 券狀態：`AVAILABLE` \| `CONSUMED` \| `SETTLED` \| `EXPIRED` |
| brand_id | String | 對應 brand 識別碼 |
| brand_name | String | 對應 brand 名稱 |
| brand_logo | String | 對應 brand logo 圖片 URL |
| campaign_id | String | 該券所屬 campaign 識別碼 |
| campaign_name | String | 該券所屬 campaign 名稱 |
| campaign_type | String | 該券所屬 campaign 類型：`auto`（系統自動兌換）\| `manual`（用戶手動兌換） |
| min_order_amount | Integer | 該券對應的消費門檻金額（元） |
| redeem_points | Integer | 兌換此券所花費的點數（coupon 建立時的快照） |
| discount_amount | Integer | 該券折抵金額（元） |
| discount_rate | Float | 每點折抵金額比率，`round(discount_amount / redeem_points, 2)`，純計算欄位 |
| max_redemptions_per_order | Integer | 該券所屬 campaign 定義的單筆交易 active campaign 券使用張數上限 |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| created_at | String | 該券建立時間（UTC+8 ISO 8601） |

### 邏輯說明
- `coupon_id` 必須屬於該 `member_id`，否則回傳 `COUPON_NOT_FOUND`
- `redeem_points` 為 coupon 建立時的快照值，不隨 campaign 規則變動
- 本 API 不回傳訂單關聯欄位，例如 `order_id`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `coupon_id` 不存在或不屬於該 `member_id`：`COUPON_NOT_FOUND`
