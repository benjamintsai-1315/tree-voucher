---
title: API Spec - update_member_selected_brands
permalink: /api-specs/update-member-selected-brands/
---

## Changelog

| Date | Summary |
| ---- | ------- |
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
  - 呼叫前必須已完成授權（`members.auth_status = AUTHORIZED`）
  - `brand_ids` 內所有 brand 都必須存在且目前具備 active auto campaign
  - `brand_ids` 陣列長度不得超過當前 active rotation 的 `max_selectable_brand_count`

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
| brand_ids | array | TRUE | 更新後的完整品牌 ID 清單；可為空陣列（代表清空全部已選品牌） |

## Request Sample

```json
{
  "member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683",
  "brand_ids": ["BRAND_711", "BRAND_COSMED"]
}
```

# Response
HTTP Status: `200 OK`（無 body）

## 邏輯說明
- 以 `brand_ids` 作為更新後完整清單；後端比對既有選擇計算 diff，將快照寫入 `member_brand_change_logs`
- `brand_ids` 可為空陣列，代表清空全部已選品牌；此情況仍視為一次品牌異動並寫入紀錄
- 本 API 為「用戶進入系統」的觸發點之一，呼叫時須先執行 lazy cleanup（詳見 background.md）

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 目前無 active rotation：`NO_ACTIVE_ROTATION`
3. `brand_id` 不存在：`BRAND_NOT_FOUND`
4. 該品牌目前無 active auto campaign：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
5. 選擇品牌數超過上限：`BRAND_SELECTION_LIMIT_EXCEEDED`
