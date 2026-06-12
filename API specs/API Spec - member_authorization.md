---
title: API Spec - member_authorization
permalink: /api-specs/member-authorization/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-12 | 由 `user_authorize` 重新設計：更名為 `member_authorization`；支援 `AUTHORIZE` / `DEAUTHORIZE` 雙向操作；神坊主動呼叫點數系統 API，兩邊皆成功才完成；`member_id` 取代 `user_id`；新增 502 `POINT_SYSTEM_ERROR` |

# API: member_authorization

## 功能說明
讓 CR 前台以 API Key 對樹享券平台發起用戶授權或解除授權。樹享券平台收到請求後，主動呼叫點數系統 API 完成對應動作；點數系統成功後，神坊更新 `members.auth_status` 並寫入 `member_authorization_logs`。兩邊皆成功才視為完成，任一失敗則整筆失敗。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為 CR 前台專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中

## 使用情境
- `action = AUTHORIZE`：用戶在 CR 前台首次同意或重新同意樹享券平台授權時呼叫
- `action = DEAUTHORIZE`：用戶在 CR 前台主動解除授權時呼叫

# Request
HTTP method: `POST`
Endpoint: `/coupon/member_authorization`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| action | string | TRUE | FALSE | ❎ | `AUTHORIZE` / `DEAUTHORIZE` |
| terms_version | string | TRUE | FALSE | ❎ | 最多 32 字 |

# Response
## Sample（JSON）

```json
{
  "member_id": "USR_000123",
  "auth_status": "AUTHORIZED",
  "terms_version": "treevoucher-v1",
  "auth_updated_at": "2026-10-01T08:00:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| member_id | String | 神坊用戶識別碼 |
| auth_status | String | 執行後的授權狀態：`AUTHORIZED` / `DEAUTHORIZED` |
| terms_version | String | 本次動作對應的條款版本 |
| auth_updated_at | String | 授權狀態最後變更時間（UTC+8 ISO 8601） |

### 邏輯說明
- 神坊收到請求後，先呼叫點數系統 API；點數系統失敗則直接回失敗，神坊狀態不變
- 點數系統成功後，神坊於同一 transaction 更新 `members.auth_status` 並寫入一筆 `member_authorization_logs`
- 同一 `member_id` 以相同 `action` 重複呼叫視為冪等，不報錯，回傳當前狀態
- 解除授權後，用戶錢包中 `AVAILABLE` 的 coupon 保留但不可使用；`PROCESSING` 的 order 繼續走完原流程
- 重新授權後，原有 `AVAILABLE` coupon 自動恢復可用，無需額外操作

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `action` 值不合法：`INVALID_ACTION`

## 502 錯誤回傳（TYPE: MESSAGE）
1. 點數系統呼叫失敗：`POINT_SYSTEM_ERROR`
