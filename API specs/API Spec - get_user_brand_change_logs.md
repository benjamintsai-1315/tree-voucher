---
title: API Spec - get_user_brand_change_logs
permalink: /api-specs/get-user-brand-change-logs/
---

# API: get_user_brand_change_logs

## 功能說明
讓樹享券平台前台端以 API Key 依 `user_id` 查詢該用戶過去品牌異動與服務狀態異動紀錄，包含首次選擇品牌、更換品牌、暫停用券與重啟用券，供前端呈現異動紀錄頁。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `user_id` 必須存在於神坊系統中
  - 僅可查詢該 `user_id` 過去 1 年內的異動紀錄

## 使用情境
前台端帶入 `user_id` 查詢該用戶過去 1 年內的品牌異動與自動兌換狀態異動紀錄，供用戶回看曾經選過哪些品牌，以及何時暫停或重啟服務。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_user_brand_change_logs`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| user_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 20 | > 0 |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 5,
  "items": [
    {
      "log_id": "BCL_20270101_00001",
      "request_id": "SYS_20270101_Q1_CLEAR",
      "action": "SYSTEM_CLEAR_BRANDS",
      "before_brand_ids": [
        "BRAND_711",
        "BRAND_COSMED"
      ],
      "after_brand_ids": [],
      "occurred_at": "2027-01-01T00:00:00+08:00"
    },
    {
      "log_id": "BCL_20261020_00003",
      "request_id": "REQ_20261020_00002",
      "action": "REMOVE_BRAND",
      "before_brand_ids": [
        "BRAND_FAMILYMART",
        "BRAND_711"
      ],
      "after_brand_ids": [
        "BRAND_711",
        "BRAND_COSMED"
      ],
      "occurred_at": "2026-10-20T11:00:00+08:00"
    },
    {
      "log_id": "BCL_20261020_00004",
      "request_id": "REQ_20261020_00002",
      "action": "ADD_BRAND",
      "before_brand_ids": [
        "BRAND_FAMILYMART",
        "BRAND_711"
      ],
      "after_brand_ids": [
        "BRAND_711",
        "BRAND_COSMED"
      ],
      "occurred_at": "2026-10-20T11:00:00+08:00"
    },
    {
      "log_id": "BCL_20261015_00002",
      "request_id": "REQ_20261015_00001",
      "action": "PAUSE",
      "before_brand_ids": [
        "BRAND_FAMILYMART",
        "BRAND_711"
      ],
      "after_brand_ids": [
        "BRAND_FAMILYMART",
        "BRAND_711"
      ],
      "occurred_at": "2026-10-15T20:30:00+08:00"
    },
    {
      "log_id": "BCL_20261001_00001",
      "request_id": "REQ_20261001_00001",
      "action": "INITIAL_SELECTION",
      "before_brand_ids": [],
      "after_brand_ids": [
        "BRAND_FAMILYMART",
        "BRAND_711"
      ],
      "occurred_at": "2026-10-01T09:00:00+08:00"
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
| items | Array | 該用戶過去 1 年內的品牌與服務狀態異動紀錄 |

### items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| log_id | String | 異動紀錄識別碼 |
| request_id | String | 同一次品牌操作批次識別碼 |
| action | String | 異動行為：`INITIAL_SELECTION` \| `ADD_BRAND` \| `REMOVE_BRAND` \| `PAUSE` \| `RESUME` \| `SYSTEM_CLEAR_BRANDS` |
| before_brand_ids | Array | 異動前品牌清單；若不適用則為空陣列 |
| after_brand_ids | Array | 異動後品牌清單；若不適用則為空陣列 |
| occurred_at | String | 異動發生時間（UTC+8 ISO 8601） |

### 邏輯說明
- 僅回傳過去 1 年內的紀錄，依 `occurred_at` 由新到舊排序
- 底層資料來源為 `brand_change_logs`
- 同一 `request_id` 代表同一次品牌設定操作；若該次操作同時包含新增與移除品牌，API 可回傳多筆相同 `request_id` 的資料列
- `before_brand_ids` / `after_brand_ids` 為查詢層 projection，由同一 `request_id` 的事件批次重建
- `PAUSE` / `RESUME` 不改變品牌清單，因此 `before_brand_ids` 與 `after_brand_ids` 可相同
- `INITIAL_SELECTION` 的 `before_brand_ids` 為空陣列
- `ADD_BRAND` / `REMOVE_BRAND` 用於表達一般品牌更換與清空全部品牌的差異事件
- `SYSTEM_CLEAR_BRANDS` 代表系統季度批次清空已選品牌；其 `after_brand_ids` 固定為空陣列
- 無任何異動紀錄時，回傳 `items: []`，不報錯

## 400 錯誤回傳（TYPE: MESSAGE）
1. `user_id` 不存在：`USER_NOT_FOUND`
