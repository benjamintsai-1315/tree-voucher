---
title: API Spec - get_current_rotation
permalink: /api-specs/get-current-rotation/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-16 | 欄位命名去除 prefix（`brand_id` → `id`、`brand_name` → `name` 等）；`description` 改回 `display_unit_cash_amount` / `display_unit_point_amount`；`rotation_id` → `id`；active_campaign 新增 `created_at`；`discount_rate` 說明改為四捨五入至小數點第二位 |
| 2026-06-15 | `active_campaign` 新增 `discount_rate` 計算欄位；此 API 僅回傳 `type = auto` 的 campaign，不回傳 `type` 欄位 |
| 2026-06-15 | 由 `get_rotation_config` 與 `get_active_brands` 合併而來；將 brands 清單納入回傳，統一為單一呼叫 |

# API: get_current_rotation

## 功能說明
讓樹享券平台前台端取得目前 active rotation（輪播檔期）的設定資訊，以及本檔期所有具備 active campaign 的品牌清單與 campaign 規則，供前端顯示活動期間、品牌選擇上限、兌換條件說明及品牌一覽頁面。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key

## 使用情境
前台端於頁面初始化時呼叫此 API，一次取得當前檔期基本設定（開始/結束時間、可選品牌數上限、顯示用說明參數）及可供用戶選擇的品牌完整清單。

> **注意：** `display_unit_cash_amount` 與 `display_unit_point_amount` 目前供前端呈現說明文字（例如：「每消費 100 元折抵 20 點」），不影響實際清算邏輯。實際清算依各品牌 campaign 的規則執行。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_current_rotation`
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
  "id": "rotation_ulid",
  "start_time": "2026-01-01T00:00:00+08:00",
  "end_time": "2026-03-31T23:59:59+08:00",
  "display_unit_cash_amount": 100,
  "display_unit_point_amount": 20,
  "max_selectable_brand_count": 3,
  "brands": [
    {
      "id": "BRAND_FAMILYMART",
      "name": "全家便利商店",
      "logo": "https://cdn.example.com/logos/familymart.png",
      "category": "便利商店",
      "active_campaign": {
        "id": "CPN_CAMP_001",
        "name": "滿100折21",
        "unit_cash_amount": 100,
        "unit_point_amount": 20,
        "unit_discount_amount": 21,
        "discount_rate": 1.05,
        "max_redeem_count": 3,
        "created_at": "2025-09-01T00:00:00+08:00",
        "updated_at": "2025-10-01T09:00:00+08:00"
      },
      "created_at": "2025-09-01T00:00:00+08:00",
      "updated_at": "2025-10-01T09:00:00+08:00"
    },
    {
      "id": "BRAND_711",
      "name": "7-ELEVEN",
      "logo": "https://cdn.example.com/logos/711.png",
      "category": "便利商店",
      "active_campaign": {
        "id": "CPN_CAMP_002",
        "name": "滿150折30",
        "unit_cash_amount": 150,
        "unit_point_amount": 25,
        "unit_discount_amount": 30,
        "discount_rate": 1.2,
        "max_redeem_count": 10,
        "created_at": "2025-10-01T00:00:00+08:00",
        "updated_at": "2025-10-01T09:00:00+08:00"
      },
      "created_at": "2025-08-01T00:00:00+08:00",
      "updated_at": "2025-10-01T09:00:00+08:00"
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 當前檔期識別碼 |
| start_time | String | 檔期開始時間（UTC+8 ISO 8601） |
| end_time | String | 檔期結束時間（UTC+8 ISO 8601） |
| display_unit_cash_amount | Integer | 顯示用單位消費金額（元），供前端呈現說明文字 |
| display_unit_point_amount | Integer | 顯示用單位兌換點數，供前端呈現說明文字 |
| max_selectable_brand_count | Integer | 本檔期用戶最多可選擇的品牌數量 |
| brands | Array | 本檔期所有具備 active auto campaign 的品牌清單 |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼 |
| name | String | 品牌名稱 |
| logo | String | 品牌 logo 圖片 URL |
| category | String | 品牌分類（例：便利商店、藥妝、超市） |
| active_campaign | Object | 該品牌當前有效的 auto campaign 規則 |
| created_at | String | 品牌建立時間（UTC+8 ISO 8601） |
| updated_at | String | 品牌資料最後更新時間（UTC+8 ISO 8601） |

### active_campaign

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | Campaign 識別碼 |
| name | String | Campaign 名稱 |
| unit_cash_amount | Integer | 每消費滿 N 元可對應使用一張券 |
| unit_point_amount | Integer | 兌換一張券所需點數 |
| unit_discount_amount | Integer | 一張券可折抵的金額（元） |
| discount_rate | Float | 每點折抵金額比率，`round(unit_discount_amount / unit_point_amount, 2)`，四捨五入至小數點第二位，純計算欄位 |
| max_redeem_count | Integer | 本檔活動最多一次可以用幾張券 |
| created_at | String | Campaign 建立時間（UTC+8 ISO 8601） |
| updated_at | String | Campaign 最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明
- 僅回傳 `type = auto` 且當前為 active rotation 的 campaign 品牌
- 每個 brand 同一時間只會有一個 active `auto` campaign，故 `active_campaign` 為單一物件而非陣列
- `discount_rate` 為 server 端計算後附帶回傳，不存於 DB
- 排列順序以 `category` 分組後，組內依 `name` 字母順序排列
- 無任何符合條件的品牌時，回傳 `brands: []`，不報錯

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `NO_ACTIVE_ROTATION` | 目前無 active rotation（未到開始時間或已過結束時間） |
