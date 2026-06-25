---
title: API Spec - update_member_selected_brands
permalink: /api-specs/update-member-selected-brands/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-25 | 由 `update_member_settings`（action=SELECT_BRANDS）拆分為獨立 endpoint；payload 改為 `brand_ids` 完整清單取代；response 改為 200 OK 無 body |

# API: update_member_selected_brands

## 功能說明
讓樹享券平台前台端以 API Key 更新該會員的已選品牌清單。以 `brand_ids` 作為更新後的完整結果，後端自行計算 diff 並寫入異動紀錄。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前必須已完成點數授權（`members.auth_status = AUTHORIZED`）
  - `brand_ids` 內所有 brand 都必須存在且目前具備 active auto campaign
  - `brand_ids` 陣列長度不得超過當前 active rotation 的 `max_selectable_brand_count`

# Request
HTTP method: `PATCH`
Endpoint: `/coupon/update_member_selected_brands`
Content-Type: `application/json`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{treecoupon_frontend_api_key}}` |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| member_id | string | TRUE | UUID |
| brand_ids | array\<string\> | TRUE | 更新後的完整品牌 ID 清單；可為空陣列（代表清空全部已選品牌） |

## Request Sample（JSON）

```json
{
  "member_id": "USR_000123",
  "brand_ids": ["BRAND_711", "BRAND_COSMED"]
}
```

# Response
HTTP Status: `200 OK`（無 body）

### 邏輯說明
- 呼叫時須先執行 **lazy cleanup**：若用戶現有 `member_selected_brands` 的 `rotation_id` 與當前 active rotation 不符，系統自動清除舊選擇並寫入異動紀錄，再繼續處理本次操作
- 以 `brand_ids` 作為更新後完整清單；後端比對既有選擇計算 diff，將快照（含品牌名稱）寫入 `member_brand_change_logs.data`（`add_brands` / `remove_brands`）
- `brand_ids` 可為空陣列，代表清空全部已選品牌；此情況仍視為一次品牌異動並寫入紀錄
- 不改變 `auto_redeem_enabled` 既有值
- lazy cleanup 清空時額外寫入一筆 system_clear 記錄（`add_brands: []`，`remove_brands` 為被清空品牌），`created_at` = 舊 rotation 的 `end_time`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 使用者尚未完成點數授權：`POINT_USAGE_NOT_AUTHORIZED`
3. 目前無 active rotation：`NO_ACTIVE_ROTATION`
4. `brand_id` 不存在：`BRAND_NOT_FOUND`
5. 該品牌目前無 active auto campaign：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
6. 選擇品牌數超過上限：`BRAND_SELECTION_LIMIT_EXCEEDED`
