---
title: API Spec - deactivate_member
permalink: /api-specs/deactivate-member/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-21 | coupon 狀態 enum 統一改為小寫（`available`/`consumed`），與 DB 一致 |
| 2026-07-17 | 補充失敗情境：點數系統失敗（含 timeout）直接回失敗、狀態不變，可安全重試；點數系統成功但樹配券本地寫入失敗屬非預期錯誤，回 5xx 並觸發 Sentry alert 人工介入 |
| 2026-07-06 | log 表以 `member_event_logs`（統一會員事件表）為權威，釐清先前 changelog 誤植的 `member_activation_logs` |
| 2026-07-05 | 比照 `activate_member`，新增同步呼叫點數系統 `member_unauthorize` 取消授權；新增 `TREELIFE_ERROR` 錯誤碼 |
| 2026-07-05 | response 改為 `200 OK`（無 body）；呼叫端不需回傳資訊，移除 `is_activated` / `last_deactivated_at` 欄位 |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | `members.auth_status`（enum `AUTHORIZED`/`DEAUTHORIZED`）欄位改為 `members.is_activated`（boolean）；`member_authorization_logs` 改為 `member_activation_logs`（action 改為 `ACTIVATE`/`DEACTIVATE`）；「授權」用語全面改為「啟用」，以 `activate_member`/`deactivate_member` 概念取代舊有 `member_authorize`/`member_unauthorize` 定義 |
| 2026-07-01 | 由 `member_unauthorize` 改名為 `deactivate_member`；response 欄位 `auth_status` 改為 `status`，值 `DEAUTHORIZED` 改為 `INACTIVE`（`members.auth_status` 資料庫欄位與 `AUTHORIZED`/`DEAUTHORIZED` enum 維持不變，API 層負責轉換） |
| 2026-06-24 | 由 `member_authorization`（action=DEAUTHORIZE）拆分為獨立 endpoint；移除 `terms_version` |

# API: deactivate_member

## 功能說明
用戶在 CR 前台主動解除樹配券服務。樹配券平台收到請求後，主動呼叫點數系統 API 完成取消授權（`member_unauthorize`）；點數系統成功後，神坊更新 `members.is_activated = FALSE` 並寫入一筆 `member_event_logs`（type = `deactivate_member`，data = null）。兩邊皆成功才視為完成，任一失敗則整筆失敗。

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
HTTP Status: `200 OK`（無 body）

> **注意：** response 不回傳任何欄位，呼叫端不需要此 API 的回傳資訊；若需查詢會員當前啟用狀態，應呼叫 `get_member_settings`。

### 邏輯說明
- 樹配券收到請求後，先檢查會員當前是否已為停用狀態（`members.is_activated = false`）
  - 是：直接回傳 `200 OK`，不重複寫 log，不呼叫點數系統
  - 否：先呼叫點數系統 API（`member_unauthorize`）取消授權；點數系統失敗則直接回失敗，樹配券狀態不變
    - 點數系統成功後，更新 `members.is_activated = false`、`members.updated_at`，並寫入一筆 `member_event_logs`（type=deactivate_member，data=null）

> **失敗情境補充：**
> - **點數系統失敗（含 timeout）**：直接回失敗（`TREELIFE_ERROR`），樹配券狀態不變；此操作具冪等性，前端可直接重試同一 API，不需額外查詢確認
> - **點數系統成功、樹配券平台後續寫入失敗**（`members` 更新或 `member_event_logs` 寫入失敗）：屬**非預期錯誤**，回 5xx 並觸發 Sentry alert 通知工程團隊人工介入；此時點數系統端已完成解除授權，但樹配券本地端狀態未同步，需人工確認並補正兩邊狀態一致，不列入下方 400 MESSAGE 清單
- 停用後，用戶錢包中 `available` 的 coupon 保留但不可用於新交易；`consumed` 狀態的 order 繼續走完原流程
- 重新啟用（呼叫 `activate_member`）後，原有 `available` coupon 自動恢復可用，無需額外操作

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 小樹生活點數系統呼叫失敗：`TREELIFE_ERROR`
