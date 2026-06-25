---
title: API Spec - get_coupon_wallet
permalink: /api-specs/get-coupon-wallet/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-23 | 重新設計為品牌摘要 API；原券列表功能移至 `get_coupons` |

# API: get_coupon_wallet

## 功能說明
查詢用戶券夾的品牌摘要。回傳該用戶在當前 rotation 曾選過的所有品牌，以及各品牌目前可用券（`AVAILABLE`）的張數，供前端呈現品牌卡片列表（券夾首頁）。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中

## 使用情境
前台端帶入 `member_id`，取得用戶目前券夾的品牌卡片摘要。前端可由此進入各品牌的券列表（`get_coupons`）。

若使用者在當前 rotation 尚未選擇任何品牌，回傳 `brands: []`，不視為錯誤。

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

# Response
## Sample（JSON）

```json
{
  "brands": [
    {
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "brand_logo": "https://cdn.example.com/logos/familymart.png",
      "available_coupon_count": 3
    },
    {
      "brand_id": "BRAND_711",
      "brand_name": "7-ELEVEN",
      "brand_logo": "https://cdn.example.com/logos/711.png",
      "available_coupon_count": 0
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brands | Array | 用戶在當前 rotation 曾選過的品牌列表 |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brand_id | String | 品牌識別碼 |
| brand_name | String | 品牌名稱 |
| brand_logo | String | 品牌 logo 圖片 URL |
| available_coupon_count | Integer | 該品牌目前狀態為 `AVAILABLE` 的券張數 |

### 邏輯說明
- 回傳用戶在**當前 rotation** 曾選過的所有品牌，包含 `available_coupon_count = 0` 的品牌（券已全部用完或尚未發券）
- `available_coupon_count` 只聚合 `status = AVAILABLE` 的券張數
- 若用戶在當前 rotation 尚未選擇任何品牌，回傳 `brands: []`，不報錯
- 排序依 `brand_name ASC`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
