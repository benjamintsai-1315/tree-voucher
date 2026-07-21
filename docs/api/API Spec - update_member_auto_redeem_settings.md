---
title: API Spec - update_member_auto_redeem_settings
permalink: /api-specs/update-member-auto-redeem-settings/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-21 | coupon 狀態 enum 統一改為小寫（`available`），與 DB 一致 |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-06-25 | 從 `update_member_settings`（action=PAUSE/RESUME）拆分為獨立 endpoint；payload 改為 `auto_redeem_enabled: boolean`；response 改為 200 OK 無 body |
| 2026-06-24 | `PAUSE` / `RESUME` 冪等說明：當前狀態已與目標一致時，直接回 200，不寫異動紀錄 |
| 2026-06-18 | 移除 `RESUME` 的 `NO_ACTIVE_SELECTED_BRANDS` 限制：用戶券夾仍可能有可用券，不應阻擋操作 |

# API: update_member_auto_redeem_setting

## 功能說明
讓樹配券平台前台端以 API Key 切換該會員的自動兌換服務狀態（暫停／啟用）。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

# Request
HTTP method: `POST`
Endpoint: `/coupon/update_member_auto_redeem_settings`
Content-Type: `application/json`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters（json）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| member_id | string | TRUE | UUID |
| auto_redeem_enabled | boolean | TRUE | `true` = 啟用自動兌換；`false` = 暫停 |

## Request Sample

```json
{
  "member_id": "17e26fe8-2bf4-4fbc-996f-f17b90fac683",
  "auto_redeem_enabled": false
}
```

# Response
HTTP Status: `200 OK`（無 body）

## 邏輯說明
- 更新 `members.auto_redeem_enabled`，新增 member_event_logs
- 冪等：若當前狀態已與目標一致，直接回 200，不重複寫異動紀錄
- 不改變已選品牌清單
- 不限制用戶當下是否有已選品牌（用戶券夾仍可能有可用券）
- 暫停後，`available` coupon 保留但刷卡時不觸發自動兌換；重啟後自動恢復

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
