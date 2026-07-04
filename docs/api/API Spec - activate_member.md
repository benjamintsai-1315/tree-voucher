---
title: API Spec - activate_member
permalink: /api-specs/activate-member/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-05 | response 改為 `200 OK`（無 body）；呼叫端不需回傳資訊，移除 `is_activated` / `last_activated_at` 欄位 |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | `members.auth_status`（enum `AUTHORIZED`/`DEAUTHORIZED`）欄位改為 `members.is_activated`（boolean）；`member_authorization_logs` 改為 `member_activation_logs`（action 改為 `ACTIVATE`/`DEACTIVATE`）；「授權」用語全面改為「啟用」，以 `activate_member` 概念取代舊有 `member_authorize` 定義 |
| 2026-07-01 | 由 `member_authorize` 改名為 `activate_member`；response 欄位 `auth_status` 改為 `status`，值 `AUTHORIZED` 改為 `ACTIVE`（`members.auth_status` 資料庫欄位與 `AUTHORIZED`/`DEAUTHORIZED` enum 維持不變，API 層負責轉換） |
| 2026-06-24 | 由 `member_authorization`（action=AUTHORIZE）拆分為獨立 endpoint；移除 `terms_version` |

# API: activate_member

## 功能說明
用戶在 CR 前台同意啟用樹享券服務。樹享券平台收到請求後，主動呼叫點數系統 API 完成授權；點數系統成功後，樹配券平台新增會員或更新 `members.is_activated = TRUE` 並寫入一筆 `member_event_logs`（type = `active_member`，data = null）。兩邊皆成功才視為完成，任一失敗則整筆失敗。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為 CR 前台專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

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
  "member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683"
}
```

# Response
HTTP Status: `200 OK`（無 body）

> **注意：** response 不回傳任何欄位，呼叫端不需要此 API 的回傳資訊；若需查詢會員當前啟用狀態，應呼叫 `get_member_settings`。

### 邏輯說明
- 樹配券收到請求後，先檢查會員是否在樹配券平台存在且服務已啟用（`members.is_activated = true`）
  - 是，直接回傳 `200 OK`，不重複寫 log
  - 否：先呼叫點數系統 API；點數系統失敗則直接回失敗，樹配券狀態不變
    - Treelife API 成功後，會員是否存在於樹配券平台
      - 是：更新 `members.is_activated` = true、`members.updated_at`。
      - 否：新增 `members`
    - 寫入一筆 `member_event_logs`（type = `activate_member`，data = null）

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在於小樹生活：`MEMBER_NOT_FOUND_IN_TREELIFE`
2. 小樹生活點數系統呼叫失敗：`TREELIFE_ERROR`
