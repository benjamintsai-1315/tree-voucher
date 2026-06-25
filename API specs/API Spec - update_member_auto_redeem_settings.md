---
title: API Spec - update_member_auto_redeem_settings
permalink: /api-specs/update-member-auto-redeem-settings/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-25 | 由 `update_member_settings`（action=PAUSE/RESUME）拆分為獨立 endpoint；payload 改為 `auto_redeem_enabled` boolean；response 改為 200 OK 無 body |

# API: update_member_auto_redeem_settings

## 功能說明
讓樹享券平台前台端以 API Key 切換該會員的自動兌換服務狀態（暫停／啟用）。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中

# Request
HTTP method: `PATCH`
Endpoint: `/coupon/update_member_auto_redeem_settings`
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
| auto_redeem_enabled | boolean | TRUE | `true` = 啟用自動兌換；`false` = 暫停 |

## Request Sample（JSON）

```json
{
  "member_id": "USR_000123",
  "auto_redeem_enabled": false
}
```

# Response
HTTP Status: `200 OK`（無 body）

### 邏輯說明
- 更新 `members.auto_redeem_enabled`
- 冪等：若當前狀態已與目標一致，直接回 200，不重複寫異動紀錄
- 不改變已選品牌清單
- 不限制用戶當下是否有已選品牌（用戶券夾仍可能有可用券）
- 暫停後，`AVAILABLE` coupon 保留但刷卡時不觸發自動兌換；重啟後自動恢復

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
