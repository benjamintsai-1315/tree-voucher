---
title: API Spec - get_active_brands
permalink: /api-specs/get-active-brands/
---

## Changelog

| Date | Summary |
| ---- | ------- |

# API: get_active_brands

## 功能說明
讓樹享券平台前台端以 API Key 取得目前所有具備 active campaign 的品牌清單及對應 campaign 詳情，供前端呈現品牌一覽頁面。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key

## 使用情境
前台端呼叫此 API 取得當前所有可供用戶選擇的品牌，每筆品牌資料附帶對應的 active campaign 規則，供前端顯示兌換條件。無 active campaign 的品牌不列入回傳。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_active_brands`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
此 API 無 request parameters。

# Response
## Sample（JSON）

```json
{
  "max_selectable_brand_count": 3,
  "brands": [
    {
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "brand_logo": "https://cdn.example.com/logos/familymart.png",
      "brand_category": "便利商店",
      "active_campaign": {
        "campaign_id": "CPN_CAMP_001",
        "campaign_name": "滿100折21",
        "unit_cash_amount": 100,      // 每消費滿 100 元可使用一張券
        "unit_point_amount": 20,      // 兌換一張券所需點數
        "unit_discount_amount": 21,   // 一張券可折抵金額（元）
        "max_redeem_count": 3,
        "updated_at": "2026-10-01T09:00:00+08:00"
      },
      "created_at": "2026-09-01T00:00:00+08:00",
      "updated_at": "2026-10-01T09:00:00+08:00"
    },
    {
      "brand_id": "BRAND_711",
      "brand_name": "7-ELEVEN",
      "brand_logo": "https://cdn.example.com/logos/711.png",
      "brand_category": "便利商店",
      "active_campaign": {
        "campaign_id": "CPN_CAMP_002",
        "campaign_name": "滿150折30",
        "unit_cash_amount": 150,
        "unit_point_amount": 25,
        "unit_discount_amount": 30,
        "max_redeem_count": 2,
        "updated_at": "2026-10-01T09:00:00+08:00"
      },
      "created_at": "2026-08-01T00:00:00+08:00",
      "updated_at": "2026-10-01T09:00:00+08:00"
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| max_selectable_brand_count | Integer | 目前環境參數允許用戶最多可選擇的品牌數量 |
| brands | Array | 所有具備 active campaign 的品牌清單 |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brand_id | String | 品牌識別碼 |
| brand_name | String | 品牌名稱 |
| brand_logo | String | 品牌 logo 圖片 URL |
| brand_category | String | 品牌分類（例：便利商店、藥妝、超市） |
| active_campaign | Object | 該品牌當前有效的 campaign 規則 |
| created_at | String | 品牌建立時間（UTC+8 ISO 8601），可作為「最新合作」的判斷依據 |
| updated_at | String | 品牌資料最後更新時間（UTC+8 ISO 8601） |

### active_campaign

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| campaign_id | String | Campaign 識別碼 |
| campaign_name | String | Campaign 名稱 |
| unit_cash_amount | Integer | 每消費滿 N 元可對應使用一張券 |
| unit_point_amount | Integer | 兌換一張券所需點數 |
| unit_discount_amount | Integer | 一張券可折抵的金額（元） |
| max_redeem_count | Integer | 單筆交易中，當前 active campaign 最多可使用幾張券 |
| updated_at | String | Campaign 最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明
- 僅回傳當前有 active campaign 的品牌，無 active campaign 的品牌不列入
- `max_selectable_brand_count` 取自當前 active rotation 的 `rotations.max_selectable_brand_count`
- 每個 brand 同一時間只會有一個 active campaign，故 `active_campaign` 為單一物件而非陣列
- 排列順序以 `brand_category` 分組後，組內依 `brand_name` 字母順序排列
- 無任何符合條件的品牌時，回傳 `brands: []`，不報錯
- 若無 active rotation，回傳 `NO_ACTIVE_ROTATION` error（400）

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `NO_ACTIVE_ROTATION` | 目前無 active rotation，無法取得品牌選擇上限 |
