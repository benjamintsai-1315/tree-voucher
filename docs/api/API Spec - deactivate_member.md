---
title: API Spec - deactivate_member
permalink: /api-specs/deactivate-member/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | `members.auth_status`（enum `AUTHORIZED`/`DEAUTHORIZED`）欄位改為 `members.is_activated`（boolean）；`member_authorization_logs` 改為 `member_activation_logs`（action 改為 `ACTIVATE`/`DEACTIVATE`）；「授權」用語全面改為「啟用」，以 `activate_member`/`deactivate_member` 概念取代舊有 `member_authorize`/`member_unauthorize` 定義 |
| 2026-07-01 | 由 `member_unauthorize` 改名為 `deactivate_member`；response 欄位 `auth_status` 改為 `status`，值 `DEAUTHORIZED` 改為 `INACTIVE`（`members.auth_status` 資料庫欄位與 `AUTHORIZED`/`DEAUTHORIZED` enum 維持不變，API 層負責轉換） |
| 2026-06-24 | 由 `member_authorization`（action=DEAUTHORIZE）拆分為獨立 endpoint；移除 `terms_version` |

# API: deactivate_member

## 功能說明
用戶在 CR 前台主動解除樹享券服務。神坊更新 `members.is_activated = FALSE` 並寫入一筆 `member_activation_logs`（action=DEACTIVATE）。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為 CR 前台專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

# Request
HTTP method: `POST`
Endpoint: `/coupon/deactivate_member`
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
HTTP Status: `200 OK`

## Response Sample（JSON）

```json
{
  "member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683",
  "status": "INACTIVE",
  "auth_updated_at": "2026-10-15T20:00:00+08:00"
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| member_id | String | 神坊用戶識別碼 |
| status | String | 執行後的服務啟用狀態，此 API 固定回傳 `INACTIVE`（對應資料庫 `members.is_activated = FALSE`） |
| auth_updated_at | String | 啟用狀態最後變更時間（UTC+8 ISO 8601） |

### 邏輯說明
- 神坊於同一 transaction 更新 `members.is_activated = FALSE`、`members.auth_updated_at`，並寫入一筆 `member_activation_logs`（action=DEACTIVATE）
- 冪等：`is_activated` 已為 `FALSE` 時重複呼叫，不重複寫 log，回傳當前狀態（`status: INACTIVE`）
- 停用後，用戶錢包中 `AVAILABLE` 的 coupon 保留但不可用於新交易；`CONSUMED` 狀態的 order 繼續走完原流程
- 重新啟用（呼叫 `activate_member`）後，原有 `AVAILABLE` coupon 自動恢復可用，無需額外操作

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
