---
title: API Spec - user_authorize
permalink: /api-specs/user-authorize/
---

# API: user_authorize

## 功能說明
讓樹享券平台前台端以 API Key 接收或確認使用者已同意樹享券平台可使用其點數的授權結果，作為後續自動兌換設定與用點清算的前置授權依據。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `user_id` 必須存在於神坊系統中

## 使用情境
前台端在使用者首次同意樹享券平台使用其點數時呼叫此 API。神坊需接收或確認該授權結果與授權時間，供後續品牌設定、自動兌換與 `create_order` 清算流程檢查；點數授權主記錄可由外部點數系統維護。

# Request
HTTP method: `POST`
Endpoint: `/coupon/user_authorize`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| user_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| terms_version | string | TRUE | FALSE | ❎ | 最多 32 字 |

# Response
## Sample（JSON）

```json
{
  "user_id": "USR_000123",
  "is_authorized": true,
  "authorized_at": "2026-10-01T08:00:00+08:00",
  "terms_version": "treevoucher-v1",
  "updated_at": "2026-10-01T08:00:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| user_id | String | 神坊用戶識別碼 |
| is_authorized | Boolean | 是否已授權樹享券平台可使用該用戶點數；成功授權後固定為 `true` |
| authorized_at | String | 使用者授權時間（UTC+8 ISO 8601） |
| terms_version | String | 本次授權所對應的條款版本 |
| updated_at | String | 授權資訊最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明
- 此 API 用於接收或確認點數授權結果，不直接處理品牌選擇或自動兌換設定
- 同一 `user_id` 再次以相同或更新的 `terms_version` 呼叫時，可視為重新確認授權結果，不報重複錯誤
- 後續 `update_user_selected_brands` 與 `create_order` 皆應以前置授權結果作為檢查依據
- 本文件不要求神坊以獨立授權主檔資料表落地保存完整授權資料

## 400 錯誤回傳（TYPE: MESSAGE）
1. API Key 非前台端授權：`CALLER_NOT_AUTHORIZED`
2. `user_id` 不存在：`USER_NOT_FOUND`
