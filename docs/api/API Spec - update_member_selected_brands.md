---
title: API Spec - update_member_selected_brands
permalink: /api-specs/update-member-selected-brands/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-02 | `max_selectable_brand_count` 更名為 `max_selectable_auto_brand_count`，明確代表僅計入具備 active `auto` campaign 品牌的可選上限；純 `manual` campaign 品牌不可被選入 `brand_ids`（既有邊界檢查「必須具備 active auto campaign」維持不變，僅欄位命名更明確） |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 授權欄位改為啟用狀態：`members.auth_status = AUTHORIZED` → `members.is_activated = TRUE`；新增對應 400 錯誤 `MEMBER_NOT_ACTIVATED`（先前僅有邊界檢查未列出對應錯誤碼）；`邏輯說明` 補充 `NO_ACTIVE_ROTATION` 與「無符合品牌」情境的差異說明 |
| 2026-07-01 | `brand_ids` 範例值改為 ULID 格式，並補上 ULID 型別註記 |
| 2026-06-25 | 由 `update_member_settings`（action=SELECT_BRANDS）調整為獨立 endpoint；payload 改為 `brand_ids` 完整清單；response 改為 200 OK 無 body |
| 2026-06-24 | `PAUSE` / `RESUME` 冪等說明（已移至 update_member_auto_redeem_settings） |
| 2026-06-18 | 移除 `RESUME` 的 `NO_ACTIVE_SELECTED_BRANDS` 限制；品牌相關錯誤僅適用於品牌選擇操作 |

# API: update_member_selected_brands

## 功能說明
讓樹享券平台前台端以 API Key 更新該會員的已選品牌清單。以 `brand_ids` 作為更新後的完整結果，後端自行計算 diff 並寫入異動紀錄。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - `brand_ids` 內所有 brand 都必須存在且目前具備 active auto campaign
  - `brand_ids` 陣列長度不得超過當前 active rotation 的 `max_selectable_auto_brand_count`
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

# Request
HTTP method: `POST`
Endpoint: `/coupon/update_member_selected_brands`
Content-Type: `application/json`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters（json）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| member_id | string | TRUE | UUID |
| brand_ids | array | TRUE | 更新後的完整品牌 ID（ULID）清單；可為空陣列（代表清空全部已選品牌） |

## Request Sample

```json
{
  "member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683",
  "brand_ids": ["01HZYAWD1V0N5V7X9Z2A4C6DHM", "01HZYBXE2W1P6W8Y1A3B5D7EJN"]
}
```

# Response
HTTP Status: `200 OK`（無 body）

## 邏輯說明
- 以 `brand_ids` 作為更新後完整清單；後端比對既有選擇計算 diff，將快照寫入 `member_brand_change_logs`
- `brand_ids` 可為空陣列，代表清空全部已選品牌；此情況仍視為一次品牌異動並寫入紀錄
- 本 API 為「用戶進入系統」的觸發點之一，呼叫時須先執行 lazy cleanup（詳見 background.md）
- `NO_ACTIVE_ROTATION` 僅代表當前**完全無 active rotation**（不在任何 rotation 的時間區間內）；若 active rotation 存在、但 `brand_ids` 對應品牌無 active auto campaign，則回傳 `BRAND_HAS_NO_ACTIVE_CAMPAIGN`，兩者不可混用

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
3. 目前無 active rotation：`NO_ACTIVE_ROTATION`
4. `brand_id` 不存在：`BRAND_NOT_FOUND`
5. 該品牌目前無 active auto campaign：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
6. 選擇品牌數超過上限：`BRAND_SELECTION_LIMIT_EXCEEDED`
