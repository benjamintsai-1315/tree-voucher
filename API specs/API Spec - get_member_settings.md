---
title: API Spec - get_member_settings
permalink: /api-specs/get-member-settings/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-15 | 由 `get_member_selected_brands` 更名為 `get_member_settings`；endpoint 改為 `/coupon/get_member_settings`，涵蓋品牌選擇與暫停／啟用狀態 |
| 2026-06-15 | `active_campaign` 新增 `discount_rate` 計算欄位；此 API 僅回傳 `type = auto` 的 campaign |
| 2026-06-12 | 由 `get_user_selected_brands` 更名；`user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: get_member_settings

## 功能說明
讓樹享券平台前台端以 API Key 依 `member_id` 取得該會員目前的完整設定狀態，包含自動兌換服務是否啟用，以及目前已選擇、且當前仍具備 active campaign 的品牌清單與對應 campaign 詳情，供前端呈現會員設定頁面。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中

## 使用情境
前台端帶入 `member_id` 取得該用戶目前的完整設定狀態，包含服務啟用狀態（`auto_redeem_enabled`）與目前已選品牌清單。

若使用者尚未選擇任何品牌，或雖曾選擇品牌但目前沒有任何 brand 仍具備 active campaign，皆回傳空陣列 `brands: []`，不視為錯誤。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_member_settings`
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
  "member_id": "USR_000123",
  "auto_redeem_enabled": true,
  "max_selectable_brand_count": 3,
  "last_changed_at": "2026-10-15T20:30:00+08:00",
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
        "discount_rate": 1.2,
        "max_redeem_count": 2,
        "updated_at": "2026-10-01T09:00:00+08:00"
      },
      "created_at": "2026-08-01T00:00:00+08:00",
      "updated_at": "2026-10-01T09:00:00+08:00"
    },
    {
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "brand_logo": "https://cdn.example.com/logos/familymart.png",
      "brand_category": "便利商店",
      "active_campaign": {
        "campaign_id": "CPN_CAMP_001",
        "campaign_name": "滿100折21",
        "unit_cash_amount": 100,
        "unit_point_amount": 20,
        "unit_discount_amount": 21,
        "discount_rate": 1.05,
        "max_redeem_count": 3,
        "updated_at": "2026-10-01T09:00:00+08:00"
      },
      "created_at": "2026-09-01T00:00:00+08:00",
      "updated_at": "2026-10-01T09:00:00+08:00"
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| member_id | String | 神坊用戶識別碼 |
| auto_redeem_enabled | Boolean | 使用者自動兌換服務是否啟用；`false` 表示目前為暫停用券狀態 |
| max_selectable_brand_count | Integer | 本檔期允許用戶最多可選擇的品牌數量；無 active rotation 時為 `null` |
| last_changed_at | String \| null | 該用戶設定狀態最近一次異動時間（UTC+8 ISO 8601）；若從未異動則為 `null` |
| brands | Array | 該用戶目前已選擇、且當前仍具備 active campaign 的品牌清單 |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brand_id | String | 品牌識別碼 |
| brand_name | String | 品牌名稱 |
| brand_logo | String | 品牌 logo 圖片 URL |
| brand_category | String | 品牌分類（例：便利商店、藥妝、超市） |
| active_campaign | Object | 該品牌當前有效的 auto campaign 規則 |
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
| discount_rate | Float | 每點折抵金額比率，`roundup(unit_discount_amount / unit_point_amount, 2)`，純計算欄位 |
| max_redeem_count | Integer | 單筆交易中，當前 active campaign 最多可使用幾張券 |
| updated_at | String | Campaign 最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明

- 本 API 為「用戶進入系統」的觸發點之一，回傳前須先執行 **lazy cleanup**：若用戶現有 `member_selected_brands` 的 `rotation_id` 與當前 active rotation 不符，系統自動清除舊選擇並寫入 `system_clear_brands` log，再回傳清除後的最新狀態
- `max_selectable_brand_count` 取自當前 active rotation 的 `rotations.max_selectable_brand_count`；若無 active rotation，則回傳 `null`
- `auto_redeem_enabled` 為使用者層級服務狀態；`PAUSE` 後為 `false`，`RESUME` 後為 `true`
- `last_changed_at` 代表該用戶設定狀態最近一次異動時間，包含首次選牌、更換品牌、`PAUSE`、`RESUME` 與 lazy cleanup 清空
- 僅回傳該用戶已選擇、且當前仍具備 `type = auto` active campaign 的品牌
- `discount_rate` 為 server 端計算後附帶回傳，不存於 DB
- 排列順序以 `brand_category` 分組後，組內依 `brand.updated_at` 由新到舊排序，時間相同時以 `brand_name` 字母順序排列
- 若使用者存在但尚未選擇任何品牌，回傳 `brands: []`，不報錯
- 若使用者曾選擇品牌，但目前所有已選品牌都已無 active campaign，回傳 `brands: []`，不報錯
- 若使用者從未發生任何設定異動，回傳 `last_changed_at: null`

## 400 錯誤回傳（TYPE: MESSAGE）
- `member_id` 不存在：`MEMBER_NOT_FOUND`
