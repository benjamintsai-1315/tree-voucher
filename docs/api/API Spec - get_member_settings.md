---
title: API Spec - get_member_settings
permalink: /api-specs/get-member-settings/
---

## Changelog

| Date | Summary |
| --- | --- |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `selected_brand_ids` 欄位說明補上 `auto` 限定詞，與邏輯說明一致（僅回傳具備 active `auto` campaign 的品牌） |
| 2026-07-01 | `selected_brand_ids` 範例值改為 ULID 格式 |
| 2026-06-12 | 由 `get_user_selected_brands` 更名；`user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND`；endpoint 改為 `/coupon/get_member_selected_brands` |
| 2026-06-24 | `selected_brand_ids` 篩選條件明確為具備 active `auto` campaign 的品牌（手動換券不影響品牌選擇狀態） |
| 2026-06-15 | `active_campaign` 新增 `discount_rate` 計算欄位；此 API 僅回傳 `type = auto` 的 campaign |
| 2026-06-16 | 由 `get_member_selected_brands` 更名為 `get_member_settings`；endpoint 改為 `/coupon/get_member_settings`，涵蓋暫停／啟用狀態 |
| 2026-06-16 | 簡化 response：移除完整品牌物件，改為只回傳 `selected_brand_ids`（仍有 active auto campaign 的已選品牌 id 清單）；移除 `brands[]` 子表格與舊版邏輯說明 |

## 功能說明

讓樹享券平台前台端以 API Key 依 `member_id` 取得該會員目前的完整設定狀態，包含自動兌換服務是否啟用，以及目前已選擇且仍具備 active auto campaign 的品牌 id 清單，供前端呈現會員設定頁面。

## 權限需求

- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
    - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
    - member_id 必須存在於小樹生活中
    - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
    - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境

前台端帶入 `member_id` 取得該用戶目前的完整設定狀態，包含服務啟用狀態（`auto_redeem_enabled`）

# Request

HTTP method: `GET`

Endpoint: `/coupon/get_member_settings?member_id`

Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| --- | --- |
| Authorization | `ApiKey {{treecoupon_frontend_api_key}}` |

## Request Parameters

（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| --- | --- | --- | --- | --- | --- |
| member_id | string | TRUE | FALSE | ❎ | UUID |

# Response

## Sample（JSON）

```json
{  
		"member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683",  
		"auto_redeem_enabled": true,  
		"last_brand_selection_changed_at": "2026-10-15T20:30:00+08:00",  
		"selected_brand_ids": ["01HZY9VC0T9M4T6W8Y1Z3B5CGK", "01HZYAWD1V0N5V7X9Z2A4C6DHM"]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| --- | --- | --- |
| member_id | UUID | 神坊用戶識別碼 |
| auto_redeem_enabled | Boolean | 使用者自動兌換服務是否啟用；`false` 表示目前為暫停用券狀態 |
| last_brand_selection_changed_at | Datetime | 該用戶最近一次品牌選擇異動時間（UTC+8 ISO 8601）；僅首次選牌或更換品牌時更新；若從未選牌則為 `null` |
| selected_brand_ids | Array | 該用戶目前已選擇、且當前仍具備 active `auto` campaign 的品牌 `id`（ULID）清單 |

### 邏輯說明

- 本 API 為「用戶進入系統」的觸發點之一，回傳前須先執行 **lazy cleanup**：若用戶現有 `member_selected_brands` 的 `rotation_id` 與當前 active rotation 不符，系統自動清除舊選擇並寫入 `system_clear_brands` log，再回傳清除後的最新狀態
- `auto_redeem_enabled` 為使用者層級服務狀態；`PAUSE` 後為 `false`，`RESUME` 後為 `true`
- `last_brand_selection_changed_at` 代表該用戶最近一次品牌選擇異動時間，僅在更換品牌時更新；`PAUSE`、`RESUME`、lazy cleanup 不影響此欄位
    - 若使用者從未進行品牌選擇，回傳 `last_brand_selection_changed_at: null`
- `selected_brand_ids` 僅回傳已選擇且當前仍具備 active auto campaign 的品牌 id，不回傳已無 active auto campaign 的品牌
- `selected_brand_ids` 以 `id` 順序排列
- 若使用者存在但尚未選擇任何品牌，回傳 `selected_brand_ids: []`，不報錯
- 若使用者曾選擇品牌，但目前所有已選品牌都已無 active auto campaign，回傳 `selected_brand_ids: []`，不報錯

## 400 錯誤回傳（TYPE: MESSAGE）

1. member_id 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
3. 目前沒有任何檔期正在進行中：`NO_ACTIVE_ROTATION`