---
title: API Spec - get_coupon_wallet
permalink: /api-specs/get-coupon-wallet/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-12 | `user_id` → `member_id`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: get_coupon_wallet

## 功能說明
讓樹享券平台前台端以 API Key 依 `member_id` 查詢該用戶的券夾列表，支援依 `brand_id` 與單一 `status` 篩選，供前端呈現可用券、處理中券與歷史券狀態。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - `brand_id` 若有帶入，必須存在於神坊系統中

## 使用情境
前台端帶入 `member_id` 查詢該用戶所有券狀態的券夾列表。若前端只想看特定品牌或特定券狀態，可搭配 `brand_id`、`status` 進行篩選。

若使用者目前沒有任何券，回傳 `coupons: []`，不視為錯誤。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_coupon_wallet`
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
| brand_id | string | FALSE | FALSE | ❎ | UUID |
| status | string | FALSE | FALSE | ❎ | 僅接受 `AVAILABLE` \| `PROCESSING` \| `COMPLETED` \| `EXPIRED` |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 3,
  "coupons": [
    {
      "coupon_id": "CPN_001",
      "status": "AVAILABLE",
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "brand_logo": "https://cdn.example.com/logos/familymart.png",
      "campaign_id": "CPN_CAMP_001",
      "campaign_name": "滿100折21",
      "unit_cash_amount": 100,
      "unit_point_amount": 20,
      "unit_discount_amount": 21,
      "max_redeem_count": 3,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "created_at": "2026-10-01T09:00:00+08:00"
    },
    {
      "coupon_id": "CPN_002",
      "status": "PROCESSING",
      "brand_id": "BRAND_711",
      "brand_name": "7-ELEVEN",
      "brand_logo": "https://cdn.example.com/logos/711.png",
      "campaign_id": "CPN_CAMP_002",
      "campaign_name": "滿150折30",
      "unit_cash_amount": 150,
      "unit_point_amount": 25,
      "unit_discount_amount": 30,
      "max_redeem_count": 2,
      "expired_at": "2026-11-30T23:59:59.999+08:00",
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
| coupons | Array | 該用戶符合篩選條件的券夾列表 |

### coupons

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| coupon_id | String | 券識別碼 |
| status | String | 券狀態：`AVAILABLE` \| `PROCESSING` \| `COMPLETED` \| `EXPIRED` |
| brand_id | String | 對應 brand 識別碼 |
| brand_name | String | 對應 brand 名稱 |
| brand_logo | String | 對應 brand logo 圖片 URL |
| campaign_id | String | 該券所屬 campaign 識別碼 |
| campaign_name | String | 該券所屬 campaign 名稱 |
| unit_cash_amount | Integer | 該券對應的消費門檻金額（元） |
| unit_point_amount | Integer | 該券建立時所對應的點數成本 |
| unit_discount_amount | Integer | 該券折抵金額（元） |
| max_redeem_count | Integer | 該券所屬 campaign 定義的單筆交易 active campaign 券使用張數上限 |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| created_at | String | 該券建立時間（UTC+8 ISO 8601） |

### 邏輯說明
- 預設回傳該用戶所有券狀態，不只 `available` / `processing`
- 若帶 `status`，僅回傳該單一狀態的券
- 若帶 `brand_id`，僅回傳該品牌底下的券
- 預設排序先依狀態 bucket：`AVAILABLE` → `PROCESSING` → `COMPLETED` → `EXPIRED`
- 同一狀態 bucket 內依 `expired_at ASC`、`created_at ASC`、`coupon_id ASC` 排序
- 無任何券時，回傳 `coupons: []`，不報錯
- 本 API 不回傳訂單關聯欄位，例如 `order_id`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `brand_id` 不存在：`BRAND_NOT_FOUND`
