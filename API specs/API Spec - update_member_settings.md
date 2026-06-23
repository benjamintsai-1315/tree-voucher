---
title: API Spec - update_member_settings
permalink: /api-specs/update-member-settings/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-23 | `PAUSE` / `RESUME` 新增冪等說明：當前狀態已與目標一致時，直接回傳現況，不寫異動 log |
| 2026-06-18 | 移除 `RESUME` 的 `NO_ACTIVE_SELECTED_BRANDS` 限制：用戶券匣仍可能有可用券，不應阻擋 PAUSE/RESUME；`NO_ACTIVE_ROTATION` / `BRAND_NOT_FOUND` 等品牌相關錯誤標注僅適用於 `SELECT_BRANDS` |
| 2026-06-16 | 由 `update_member_selected_brands` 更名為 `update_member_settings`；endpoint 改為 `/coupon/update_member_settings`；response 改為與 `get_member_settings` 對齊，只回傳 `selected_brand_ids`，移除完整品牌物件、`max_selectable_brand_count`、`updated_at`；`last_changed_at` 改名為 `last_brand_selection_changed_at` |
| 2026-06-16 | `brands[]` 欄位去除多餘 prefix：`brand_id/name/logo/category` → `id/name/logo/category`；`active_campaign.campaign_id/name` → `id/name` |
| 2026-06-12 | 由 `update_user_selected_brands` 更名；`user_id` → `member_id`；`user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: update_member_settings

## 功能說明
讓樹享券平台前台端以 API Key 更新該會員的設定，統一處理首次選擇品牌、更換品牌、暫停用券與重啟用券。成功後回傳與 `get_member_settings` 格式一致的最新狀態，供前端直接刷新畫面。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前必須已完成點數授權，且神坊系統可取得或驗證該授權結果
  - `SELECT_BRANDS` 時，`after_brand_ids` 內所有 `brand` 都必須存在且目前具備 active auto campaign

## 使用情境
前台端以 `action` 區分本次操作：

- `SELECT_BRANDS`：設定或更新已選品牌清單，使用 `after_brand_ids` 作為更新後完整結果
- `PAUSE`：暫停用券，不變更已選品牌清單
- `RESUME`：重啟用券，不變更已選品牌清單

# Request
HTTP method: `PATCH`
Endpoint: `/coupon/update_member_settings`
Content-Type: `application/json`

## Request Header

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
  "auto_redeem_enabled": true,
  "last_brand_selection_changed_at": "2026-10-15T20:30:00+08:00",
  "selected_brand_ids": ["BRAND_711", "BRAND_FAMILYMART"]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| member_id | String | 神坊用戶識別碼 |
| auto_redeem_enabled | Boolean | 使用者自動兌換服務是否啟用；`false` 表示目前為暫停用券狀態 |
| last_brand_selection_changed_at | Datetime | 該用戶最近一次品牌選擇異動時間（UTC+8 ISO 8601）；僅首次選牌或更換品牌時更新；若從未選牌則為 `null` |
| selected_brand_ids | Array | 該用戶目前已選擇、且當前仍具備 active auto campaign 的品牌 `id` 清單 |

### 邏輯說明
- 本 API 為「用戶進入系統」的觸發點之一，呼叫時須先執行 **lazy cleanup**：若用戶現有 `member_selected_brands` 的 `rotation_id` 與當前 active rotation 不符，系統自動清除舊選擇，並寫入 `system_clear_brands` log，再繼續處理本次操作
- `SELECT_BRANDS` 以 `after_brand_ids` 作為更新後完整清單；系統以既有品牌設定與 `after_brand_ids` 比對，判定本次為首次選擇或更換品牌
- `after_brand_ids` 可為空陣列，代表清空全部已選品牌；此情況仍視為一次品牌異動
- `SELECT_BRANDS` 不改變 `auto_redeem_enabled` 既有值
- `PAUSE` / `RESUME` 不改變品牌清單；僅切換 `auto_redeem_enabled`；不限制用戶當下是否有已選品牌（用戶券匣仍可能有可用券）
- `PAUSE` / `RESUME` 為冪等操作：若當前狀態已與目標一致（例如已啟用再送 `RESUME`），直接回傳當前最新狀態，不寫異動 log
- `selected_brand_ids` 僅回傳已選擇且當前仍具備 active auto campaign 的品牌 id，與 `get_member_settings` 一致
- `selected_brand_ids` 以 `id` 順序排列
- `last_brand_selection_changed_at` 僅在首次選牌、更換品牌（`SELECT_BRANDS`）時更新；`PAUSE`、`RESUME`、lazy cleanup 不影響此欄位
- 異動紀錄寫入規則：
  - 同一個品牌設定操作共用同一個 `request_id`
  - 首次有品牌選擇時，寫入 `initial_selection`
  - 後續品牌集合變更時，預先計算 diff 寫入 `change_brand`（含 `added_brand_ids` / `removed_brand_ids`）
  - `PAUSE` / `RESUME` 各寫入對應類型的異動紀錄
  - lazy cleanup 清空時寫入 `system_clear_brands`，`created_at` = 舊 rotation 的 `end_time`
  - 底層異動表為 `member_brand_change_logs`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 使用者尚未完成點數授權：`POINT_USAGE_NOT_AUTHORIZED`
3. 目前無 active rotation（僅 `SELECT_BRANDS` 時）：`NO_ACTIVE_ROTATION`
4. `brand_id` 不存在（僅 `SELECT_BRANDS` 時）：`BRAND_NOT_FOUND`
5. 該品牌目前無 active auto campaign（僅 `SELECT_BRANDS` 時）：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
6. 選擇品牌數超過上限（僅 `SELECT_BRANDS` 時）：`BRAND_SELECTION_LIMIT_EXCEEDED`
