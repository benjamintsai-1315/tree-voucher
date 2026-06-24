---
title: API Spec - get_member_settings_change_logs
permalink: /api-specs/get-member-settings-change-logs/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-24 | `limit` 上限改為 20 筆；移除 `initial_selection` type（一律寫為 `change_brand`）；各 brand array 統一改為 `data` dict（`before_brand_ids` / `after_brand_ids`）；`pause`/`resume` 不回傳 `data` |
| 2026-06-22 | 由 `get_member_brand_change_logs` 更名；endpoint 改為 `/coupon/get_member_settings_change_logs`；品牌陣列展開品牌資訊 |
| 2026-06-15 | 回傳結構改為 request 粒度；`occurred_at` → `created_at` |
| 2026-06-12 | 由 `get_user_brand_change_logs` 更名；`user_id` → `member_id` |

# API: get_member_settings_change_logs

## 功能說明
讓樹享券平台前台端以 API Key 依 `member_id` 查詢該會員過去品牌設定與服務狀態的異動紀錄，供前端呈現異動歷程頁。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 僅回傳過去 1 年內的異動紀錄

## 使用情境
前台端帶入 `member_id` 查詢該會員過去 1 年內的設定異動紀錄，供會員回看曾經的品牌選擇變更與服務暫停／啟用歷程。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_member_settings_change_logs`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 20 | 1–20；超過 20 回 400 |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 4,
  "items": [
    {
      "type": "system_clear_brands",
      "data": {
        "before_brand_ids": ["BRAND_FAMILYMART"],
        "after_brand_ids": []
      },
      "created_at": "2027-01-01T00:00:00+08:00"
    },
    {
      "type": "change_brand",
      "data": {
        "before_brand_ids": ["BRAND_FAMILYMART"],
        "after_brand_ids": ["BRAND_COSMED"]
      },
      "created_at": "2026-10-20T11:00:00+08:00"
    },
    {
      "type": "pause",
      "created_at": "2026-10-15T20:30:00+08:00"
    },
    {
      "type": "change_brand",
      "data": {
        "before_brand_ids": [],
        "after_brand_ids": ["BRAND_FAMILYMART"]
      },
      "created_at": "2026-10-01T09:00:00+08:00"
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| page | Integer | 當前頁碼，從 1 開始 |
| limit | Integer | 每頁筆數 |
| total | Integer | 符合條件的總筆數 |
| items | Array | 該用戶過去 1 年內的設定異動紀錄 |

### items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| type | String | 操作類型：`change_brand` \| `pause` \| `resume` \| `system_clear_brands` |
| data | Object \| 省略 | 品牌異動快照；**僅 `change_brand` 與 `system_clear_brands` 回傳，`pause`/`resume` 省略** |
| created_at | String | 操作發生時間（UTC+8 ISO 8601） |

### data

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| before_brand_ids | Array | 異動前的品牌 ID 清單；首次選牌時為 `[]` |
| after_brand_ids | Array | 異動後的品牌 ID 清單；系統清空時為 `[]` |

### 邏輯說明
- 依 `created_at` 由新到舊排序，僅回傳過去 1 年內紀錄
- `initial_selection`（首次選牌）與 `change_brand`（更換品牌）統一以 `change_brand` 回傳；首次選牌時 `before_brand_ids = []`
- `pause` / `resume`：服務暫停／重啟，回傳 type 但省略 `data`
- `system_clear_brands`：系統 lazy cleanup 清空舊檔期，`before_brand_ids` 為被清空的品牌、`after_brand_ids` 為 `[]`；`created_at` 為舊 rotation 的 `end_time`
- 無任何異動紀錄時，回傳 `items: []`，不報錯

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `limit` 超過 20：`LIMIT_EXCEEDED`
