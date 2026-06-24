---
title: API Spec - get_current_rotation
permalink: /api-specs/get-current-rotation/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-24 | 邏輯說明更新：active campaign 判斷改為透過 `rotation_campaigns` join，而非 `campaigns.rotation_id` 直接比對 |
| 2026-06-24 | `active_campaign`（單一物件）改為 `campaigns`（陣列）；新增 `type` 欄位（`auto`\|`manual`）；回傳該品牌所有 active campaign，前端依 `type` 自行篩選顯示 |
| 2026-06-16 | `display_coupon_min_order_amount` / `display_coupon_redeem_points` 合併為 `description`（JSON 字串，格式 `{"order_amount": N, "point_amount": N}`），由前端自行 parse 呈現 |
| 2026-06-16 | 欄位命名去除 prefix（`brand_id` → `id`、`brand_name` → `name` 等）；`description` 改回 `display_coupon_min_order_amount` / `display_coupon_redeem_points`；`rotation_id` → `id`；active_campaign 新增 `created_at`；`discount_rate` 說明改為四捨五入至小數點第二位 |
| 2026-06-15 | `active_campaign` 新增 `discount_rate` 計算欄位；此 API 僅回傳 `type = auto` 的 campaign，不回傳 `type` 欄位 |
| 2026-06-15 | 由 `get_rotation_config` 與 `get_active_brands` 合併而來；將 brands 清單納入回傳，統一為單一呼叫 |

# API: get_current_rotation

## 功能說明
讓樹享券平台前台端取得目前 active rotation（輪播檔期）的設定資訊，以及本檔期所有具備 active campaign 的品牌清單與 campaign 規則，供前端顯示活動期間、品牌選擇上限、兌換條件說明及品牌一覽頁面。每個品牌回傳其所有 active campaign（`auto` 與 `manual`），前端依 `type` 篩選各頁面所需顯示的類型。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key

## 使用情境
前台端於頁面初始化時呼叫此 API，一次取得當前檔期基本設定（開始/結束時間、可選品牌數上限、顯示用說明參數）及可供用戶選擇的品牌完整清單。

> **注意：** `description` 為顯示用說明參數，格式為 JSON 字串（`{"order_amount": N, "point_amount": N}`），由前端自行 parse 後組合說明文字（例如：「每消費 100 元可兌換 20 點折抵」），不影響實際清算邏輯。實際清算依各品牌 campaign 的規則執行。

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
  "description": "{\"order_amount\": 100, \"point_amount\": 20}",
  "max_selectable_brand_count": 3,
  "brands": [
    {
      "id": "BRAND_FAMILYMART",
      "name": "全家便利商店",
      "logo": "https://cdn.example.com/logos/familymart.png",
      "category": "便利商店",
      "campaigns": [
        {
          "id": "CPN_CAMP_001",
          "type": "auto",
          "name": "滿100折21",
          "coupon_min_order_amount": 100,
          "coupon_redeem_points": 20,
          "coupon_discount_amount": 21,
          "discount_rate": 1.05,
          "max_redemptions_per_order": 3,
          "created_at": "2025-09-01T00:00:00+08:00",
          "updated_at": "2025-10-01T09:00:00+08:00"
        },
        {
          "id": "CPN_CAMP_001M",
          "type": "manual",
          "name": "手動換券活動",
          "coupon_min_order_amount": 100,
          "coupon_redeem_points": 20,
          "coupon_discount_amount": 21,
          "discount_rate": 1.05,
          "max_redemptions_per_order": 3,
          "created_at": "2025-09-01T00:00:00+08:00",
          "updated_at": "2025-10-01T09:00:00+08:00"
        }
      ],
      "created_at": "2025-09-01T00:00:00+08:00",
      "updated_at": "2025-10-01T09:00:00+08:00"
    },
    {
      "id": "BRAND_711",
      "name": "7-ELEVEN",
      "logo": "https://cdn.example.com/logos/711.png",
      "category": "便利商店",
      "campaigns": [
        {
          "id": "CPN_CAMP_002",
          "type": "auto",
          "name": "滿150折30",
          "coupon_min_order_amount": 150,
          "coupon_redeem_points": 25,
          "coupon_discount_amount": 30,
          "discount_rate": 1.2,
          "max_redemptions_per_order": 10,
          "created_at": "2025-10-01T00:00:00+08:00",
          "updated_at": "2025-10-01T09:00:00+08:00"
        }
      ],
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
| description | String | 顯示用說明參數，JSON 字串格式：`{"order_amount": N, "point_amount": N}`，由前端自行 parse 呈現，不影響清算 |
| max_selectable_brand_count | Integer | 本檔期用戶最多可選擇的品牌數量 |
| brands | Array | 本檔期所有具備至少一個 active campaign 的品牌清單 |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼 |
| name | String | 品牌名稱 |
| logo | String | 品牌 logo 圖片 URL |
| category | String | 品牌分類（例：便利商店、藥妝、超市） |
| campaigns | Array | 該品牌當前所有 active campaign 規則（含 `auto` 與 `manual`） |
| created_at | String | 品牌建立時間（UTC+8 ISO 8601） |
| updated_at | String | 品牌資料最後更新時間（UTC+8 ISO 8601） |

### campaigns

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | Campaign 識別碼 |
| type | String | Campaign 類型：`auto`（系統自動兌換）\| `manual`（用戶手動兌換） |
| name | String | Campaign 名稱 |
| coupon_min_order_amount | Integer | 每消費滿 N 元可對應使用一張券 |
| coupon_redeem_points | Integer | 兌換一張券所需點數 |
| coupon_discount_amount | Integer | 一張券可折抵的金額（元） |
| discount_rate | Float | 每點折抵金額比率，`round(coupon_discount_amount / coupon_redeem_points, 2)`，四捨五入至小數點第二位，純計算欄位 |
| max_redemptions_per_order | Integer | 本檔活動最多一次可以用幾張券 |
| created_at | String | Campaign 建立時間（UTC+8 ISO 8601） |
| updated_at | String | Campaign 最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明
- 回傳當前 active rotation 下所有具備至少一個 active campaign 的品牌
- campaign 的 active 判斷：`rotation_campaigns` 中是否存在 `rotation_id = 當前 active rotation` 且 `campaign_id = 該 campaign` 的記錄
- 每個 brand 的 `campaigns` 陣列包含 `auto` 與 `manual` 兩種類型；同一 brand 同一時間最多一個 `type = auto` 的 active campaign
- 前端依 `type` 篩選所需呈現的 campaign：自動兌換頁面取 `type = auto`，手動換券頁面取 `type = manual`
- `discount_rate` 為 server 端計算後附帶回傳，不存於 DB
- 排列順序以 `category` 分組後，組內依 `name` 字母順序排列
- 無任何符合條件的品牌時，回傳 `brands: []`，不報錯

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `NO_ACTIVE_ROTATION` | 目前無 active rotation（未到開始時間或已過結束時間） |
