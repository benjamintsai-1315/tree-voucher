---
title: API Spec - update_user_selected_brands
permalink: /api-specs/update-user-selected-brands/
---

# API: update_user_selected_brands

## 功能說明
讓樹享券平台前台端以 API Key 更新該用戶的已選品牌設定，統一處理首次選擇品牌、更換品牌、暫停用券與重啟用券，並回傳與 `get_user_selected_brands` 對齊的最新狀態。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `user_id` 必須存在於神坊系統中
  - 呼叫前必須已完成點數授權，且神坊系統可取得或驗證該授權結果
  - `SELECT_BRANDS` 時，`after_brand_ids` 內所有 `brand` 都必須存在且目前具備 active campaign

## 使用情境
前台端以 `action` 區分本次操作：

- `SELECT_BRANDS`：設定或更新已選品牌清單，使用 `after_brand_ids` 作為更新後完整結果
- `PAUSE`：暫停用券，不變更已選品牌清單
- `RESUME`：重啟用券，不變更已選品牌清單

成功後回傳當前最新狀態，供前端直接刷新品牌設定畫面，不必再額外呼叫 `get_user_selected_brands`。

# Request
HTTP method: `PATCH`
Endpoint: `/coupon/update_user_selected_brands`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| user_id | string | TRUE | FALSE | ❎ | UUID |
| action | string | TRUE | FALSE | ❎ | 僅接受 `SELECT_BRANDS` \| `PAUSE` \| `RESUME` |
| after_brand_ids | array<string> | FALSE | FALSE | ❎ | 僅 `action = SELECT_BRANDS` 時必填；可為空陣列；陣列長度不得超過品牌上限 |

# Response
## Sample（JSON）

```json
{
  "user_id": "USR_000123",
  "auto_redeem_enabled": true,
  "brands": [
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
  ],
  "updated_at": "2026-10-15T20:30:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| user_id | String | 神坊用戶識別碼 |
| auto_redeem_enabled | Boolean | 使用者自動兌換服務是否啟用；`false` 表示目前為暫停用券狀態 |
| brands | Array | 該用戶目前已選擇、且當前仍具備 active campaign 的品牌清單 |
| updated_at | String | 本次更新完成時間（UTC+8 ISO 8601） |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brand_id | String | 品牌識別碼 |
| brand_name | String | 品牌名稱 |
| brand_logo | String | 品牌 logo 圖片 URL |
| brand_category | String | 品牌分類（例：便利商店、藥妝、超市） |
| active_campaign | Object | 該品牌當前有效的 campaign 規則 |
| created_at | String | 品牌建立時間（UTC+8 ISO 8601） |
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
- `SELECT_BRANDS` 以 `after_brand_ids` 作為更新後完整清單；系統以既有品牌設定與 `after_brand_ids` 比對，判定本次為首次選擇或更換品牌
- `after_brand_ids` 可為空陣列，代表清空全部已選品牌；此情況仍視為一次品牌異動
- `SELECT_BRANDS` 不改變 `auto_redeem_enabled` 既有值
- `PAUSE` / `RESUME` 不改變品牌清單；僅切換 `auto_redeem_enabled`
- `RESUME` 時，若該用戶目前沒有任何已選且具 active campaign 的品牌，應回 business error
- 回傳的 `brands` 規則與 `get_user_selected_brands` 一致：只回 selected active brands
- 異動紀錄寫入規則：
  - 同一個品牌設定操作共用同一個 `request_id`
  - 首次有品牌選擇時，依 `after_brand_ids` 寫入多筆 `INITIAL_SELECTION`
  - 後續品牌集合變更時，逐一比較前後差異，按品牌寫入多筆 `ADD_BRAND` / `REMOVE_BRAND`
  - `PAUSE` / `RESUME` 依原 action 寫入單筆異動紀錄，且 `brand_id = null`
  - 底層異動表為 `brand_change_logs`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `user_id` 不存在：`USER_NOT_FOUND`
2. 使用者尚未完成點數授權：`POINT_USAGE_NOT_AUTHORIZED`
3. `brand_id` 不存在：`BRAND_NOT_FOUND`
4. 該品牌目前無 active campaign：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
5. 選擇品牌數超過上限：`BRAND_SELECTION_LIMIT_EXCEEDED`
6. 超過每月更換次數限制：`BRAND_CHANGE_LIMIT_EXCEEDED`
7. 目前無可恢復的已選有效品牌：`NO_ACTIVE_SELECTED_BRANDS`
