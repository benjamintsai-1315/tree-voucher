---
title: API Spec - update_member_selected_brands
permalink: /api-specs/update-member-selected-brands/
---

> **⚠️ Legacy：** 此規格已由 [`update_member_settings`](API%20Spec%20-%20update_member_settings.md) 取代，請勿使用本文件。

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-18 | 移除 `RESUME` 的 `NO_ACTIVE_SELECTED_BRANDS` 限制：用戶券匣仍可能有可用券，不應阻擋 PAUSE/RESUME |
| 2026-06-16 | 對齊 schema：`rotation_key` → `rotation_id`；`brand_change_logs` → `member_brand_change_logs`；異動紀錄改為 request-level 模型（`change_brand` + JSON diffs） |
| 2026-06-16 | `brands[]` 欄位去除多餘 prefix：`brand_id/name/logo/category` → `id/name/logo/category`；`active_campaign.campaign_id/name` → `id/name` |
| 2026-06-12 | 由 `update_user_selected_brands` 更名；`user_id` → `member_id`；`user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND`；endpoint 改為 `/coupon/update_member_selected_brands` |

# API: update_member_selected_brands

## 功能說明
讓樹享券平台前台端以 API Key 更新該會員的已選品牌設定，統一處理首次選擇品牌、更換品牌、暫停用券與重啟用券，並回傳與 `get_member_selected_brands` 對齊的最新狀態。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前必須已完成點數授權，且神坊系統可取得或驗證該授權結果
  - `SELECT_BRANDS` 時，`after_brand_ids` 內所有 `brand` 都必須存在且目前具備 active campaign

## 使用情境
前台端以 `action` 區分本次操作：

- `SELECT_BRANDS`：設定或更新已選品牌清單，使用 `after_brand_ids` 作為更新後完整結果
- `PAUSE`：暫停用券，不變更已選品牌清單
- `RESUME`：重啟用券，不變更已選品牌清單

成功後回傳當前最新狀態，供前端直接刷新品牌設定畫面，不必再額外呼叫 `get_member_selected_brands`。

# Request
HTTP method: `PATCH`
Endpoint: `/coupon/update_member_selected_brands`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | UUID |
| action | string | TRUE | FALSE | ❎ | 僅接受 `SELECT_BRANDS` \| `PAUSE` \| `RESUME` |
| after_brand_ids | array<string> | FALSE | FALSE | ❎ | 僅 `action = SELECT_BRANDS` 時必填；可為空陣列；陣列長度不得超過品牌上限 |

# Response
## Sample（JSON）

```json
{
  "member_id": "USR_000123",
  "max_selectable_brand_count": 3,
  "auto_redeem_enabled": true,
  "last_changed_at": "2026-10-15T20:30:00+08:00",
  "brands": [
    {
      "id": "BRAND_711",
      "name": "7-ELEVEN",
      "logo": "https://cdn.example.com/logos/711.png",
      "category": "便利商店",
      "active_campaign": {
        "id": "CPN_CAMP_002",
        "name": "滿150折30",
        "coupon_min_order_amount": 150,
        "coupon_redeem_points": 25,
        "coupon_discount_amount": 30,
        "max_redemptions_per_order": 2,
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
| member_id | String | 神坊用戶識別碼 |
| max_selectable_brand_count | Integer | 目前環境參數允許用戶最多可選擇的品牌數量 |
| auto_redeem_enabled | Boolean | 使用者自動兌換服務是否啟用；`false` 表示目前為暫停用券狀態 |
| last_changed_at | String \| null | 該用戶品牌設定狀態最近一次異動時間（UTC+8 ISO 8601）；若從未異動則為 `null` |
| brands | Array | 該用戶目前已選擇、且當前仍具備 active campaign 的品牌清單 |
| updated_at | String | 本次更新完成時間（UTC+8 ISO 8601） |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼 |
| name | String | 品牌名稱 |
| logo | String | 品牌 logo 圖片 URL |
| category | String | 品牌分類（例：便利商店、藥妝、超市） |
| active_campaign | Object | 該品牌當前有效的 campaign 規則 |
| created_at | String | 品牌建立時間（UTC+8 ISO 8601） |
| updated_at | String | 品牌資料最後更新時間（UTC+8 ISO 8601） |

### active_campaign

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | Campaign 識別碼 |
| name | String | Campaign 名稱 |
| coupon_min_order_amount | Integer | 每消費滿 N 元可對應使用一張券 |
| coupon_redeem_points | Integer | 兌換一張券所需點數 |
| coupon_discount_amount | Integer | 一張券可折抵的金額（元） |
| max_redemptions_per_order | Integer | 單筆交易中，當前 active campaign 最多可使用幾張券 |
| updated_at | String | Campaign 最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明
- 本 API 為「用戶進入系統」的觸發點之一，呼叫時須先執行 **lazy cleanup**：若用戶現有 `member_selected_brands` 的 `rotation_id` 與當前 active rotation 的 `id` 不符，系統自動清除舊選擇，寫入一筆 `system_clear_brands` 事件（`created_at` = 舊 rotation 的 `end_time`），再繼續處理本次操作
- `SELECT_BRANDS` 以 `after_brand_ids` 作為更新後完整清單；系統以既有品牌設定與 `after_brand_ids` 比對，判定本次為首次選擇或更換品牌
- `after_brand_ids` 可為空陣列，代表清空全部已選品牌；此情況仍視為一次品牌異動
- `SELECT_BRANDS` 時，同步將當前 active rotation 的 `id` 寫入 `member_selected_brands.rotation_id`
- 回傳中的 `max_selectable_brand_count` 取自當前 active rotation 的 `rotations.max_selectable_brand_count`
- `SELECT_BRANDS` 不改變 `auto_redeem_enabled` 既有值
- `PAUSE` / `RESUME` 不改變品牌清單；僅切換 `auto_redeem_enabled`；不限制用戶當下是否有已選品牌（用戶券匣仍可能有可用券）
- 回傳的 `brands` 規則與 `get_member_settings` 一致：只回 selected active brands
- `last_changed_at` 代表該用戶品牌設定狀態最近一次異動時間，包含首次選牌、更換品牌、清空品牌、`PAUSE`、`RESUME` 與 lazy cleanup 清空
- 異動紀錄寫入規則（底層表：`member_brand_change_logs`）：
  - 每次操作寫入一筆，共用同一個 `request_id`
  - 首次有品牌選擇時，`type = initial_selection`
  - 後續品牌集合變更時，`type = change_brand`，`added_brand_ids` / `removed_brand_ids` 於寫入時預先計算存入
  - `PAUSE` / `RESUME` 依原 action 寫入 `type = pause` / `type = resume`，不關聯特定品牌
  - lazy cleanup 清空時，寫入一筆 `type = system_clear_brands`，`created_at` = 舊 rotation 的 `end_time`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 使用者尚未完成點數授權：`POINT_USAGE_NOT_AUTHORIZED`
3. 目前無 active rotation（僅 `SELECT_BRANDS` 時）：`NO_ACTIVE_ROTATION`
4. `brand_id` 不存在（僅 `SELECT_BRANDS` 時）：`BRAND_NOT_FOUND`
5. 該品牌目前無 active campaign（僅 `SELECT_BRANDS` 時）：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
6. 選擇品牌數超過上限（僅 `SELECT_BRANDS` 時）：`BRAND_SELECTION_LIMIT_EXCEEDED`
