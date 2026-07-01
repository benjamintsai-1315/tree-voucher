---
title: API Spec - activate_member
permalink: /api-specs/activate-member/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-01 | 由 `member_authorize` 改名為 `activate_member`；response 欄位 `auth_status` 改為 `status`，值 `AUTHORIZED` 改為 `ACTIVE`（`members.auth_status` 資料庫欄位與 `AUTHORIZED`/`DEAUTHORIZED` enum 維持不變，API 層負責轉換） |
| 2026-06-24 | 由 `member_authorization`（action=AUTHORIZE）拆分為獨立 endpoint；移除 `terms_version` |

# API: activate_member

## 功能說明
用戶在 CR 前台同意啟用樹享券服務。樹享券平台收到請求後，主動呼叫點數系統 API 完成授權；點數系統成功後，神坊更新 `members.auth_status = AUTHORIZED` 並寫入一筆 `member_authorization_logs`（action=AUTHORIZE）。兩邊皆成功才視為完成，任一失敗則整筆失敗。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為 CR 前台專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中

# Request
HTTP method: `POST`
Endpoint: `/coupon/activate_member`
Content-Type: `application/json`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{treecoupon_frontend_api_key}}` |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| member_id | string | TRUE | 最多 64 字 |

## Request Sample（JSON）

```json
{
  "member_id": "USR_000123"
}
```

# Response
HTTP Status: `200 OK`

## Response Sample（JSON）

```json
{
  "member_id": "USR_000123",
  "status": "ACTIVE",
  "auth_updated_at": "2026-10-01T08:00:00+08:00"
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| member_id | String | 神坊用戶識別碼 |
| status | String | 執行後的服務啟用狀態，此 API 固定回傳 `ACTIVE`（對應資料庫 `members.auth_status = AUTHORIZED`） |
| auth_updated_at | String | 授權狀態最後變更時間（UTC+8 ISO 8601） |

### 邏輯說明
- 神坊收到請求後，先呼叫點數系統 API；點數系統失敗則直接回失敗，神坊狀態不變
- 點數系統成功後，神坊於同一 transaction 更新 `members.auth_status = AUTHORIZED`、`members.auth_updated_at`，並寫入一筆 `member_authorization_logs`（action=AUTHORIZE）
- 冪等：`auth_status` 已為 `AUTHORIZED` 時重複呼叫，不重複寫 log，回傳當前狀態（`status: ACTIVE`）

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`

## 502 錯誤回傳（TYPE: MESSAGE）
1. 點數系統呼叫失敗：`POINT_SYSTEM_ERROR`
