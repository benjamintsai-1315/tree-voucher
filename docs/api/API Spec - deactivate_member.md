---
title: API Spec - deactivate_member
permalink: /api-specs/deactivate-member/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-22 | 決議調整成敗判定：改為樹配券本地寫入成功即回覆成功，點數系統呼叫（`member_unauthorize`）改為 best-effort，失敗不影響回應、改觸發告警處理；移除 `TREELIFE_ERROR` 錯誤碼（不再是本 API 失敗情境）；此調整**僅適用 deactivate_member**，`activate_member` 維持原設計（點數系統成功才寫入本地，兩者不對稱） |
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
用戶在 CR 前台主動解除樹配券服務。樹配券平台收到請求後，更新 `members.is_activated = FALSE` 並寫入一筆 `member_event_logs`（type = `deactivate_member`，data = null），**樹配券本地寫入成功即視為本次請求成功**；同時呼叫點數系統 API 取消授權（`member_unauthorize`），此呼叫為 best-effort，其成功與否不影響本次 API 回應結果——若點數系統呼叫失敗，觸發告警通知工程團隊另行處理，不需等待點數系統成功才回覆成功。

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
  - 否：更新 `members.is_activated = false`、`members.updated_at`，並寫入一筆 `member_event_logs`（type=deactivate_member，data=null）；本地寫入成功即回傳 `200 OK`
    - 同時呼叫點數系統 API（`member_unauthorize`）取消授權，此呼叫為 best-effort，不影響本次回應結果

> **失敗情境補充：**
> - **樹配券本地寫入失敗**（`members` 更新或 `member_event_logs` 寫入失敗）：屬**非預期錯誤**，回 5xx；此為唯一影響本次 API 成敗判定的情境
> - **點數系統呼叫失敗（含 timeout）**：**不影響本次 API 回應**，仍回 `200 OK`；觸發告警通知工程團隊，另行確認並補正點數系統端的授權狀態，使其與樹配券本地狀態一致；不列入下方 400 MESSAGE 清單
- 停用後，用戶錢包中 `available` 的 coupon 保留但不可用於新交易；`consumed` 狀態的 order 繼續走完原流程
- 重新啟用（呼叫 `activate_member`）後，原有 `available` coupon 自動恢復可用，無需額外操作

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`

> `TREELIFE_ERROR` 已移除：點數系統呼叫失敗不再是本 API 的失敗情境，改以告警處理（見上「失敗情境補充」）。
