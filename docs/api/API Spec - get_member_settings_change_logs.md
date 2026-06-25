---
title: API Spec - get_member_settings_change_logs
permalink: /api-specs/get-member-settings-change-logs/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-22 | 由 `get_member_brand_change_logs` 更名；endpoint 改為 `/coupon/get_member_settings_change_logs`；`initial_selection` 新增 `selected_brands`、`system_clear_brands` 新增 `cleared_brands`；`change_brand` 的 `added_brand_ids`/`removed_brand_ids` 改為 `added_brands`/`removed_brands`（展開品牌資訊，支援已失效品牌） |
| 2026-06-15 | 回傳結構改為 request 粒度（一筆 = 一次操作）；diff 於寫入時預先計算，`change_brand` 類型才展開 `added_brand_ids`/`removed_brand_ids`；`occurred_at` → `created_at` |
| 2026-06-12 | 由 `get_user_brand_change_logs` 更名；`user_id` → `member_id`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND`；endpoint 改為 `/coupon/get_member_brand_change_logs` |

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
| limit | integer | FALSE | FALSE | 20 | > 0 |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 4,
  "items": [
    {
      "request_id": "SYS_20270101_Q1_CLEAR",
      "type": "system_clear_brands",
      "cleared_brands": [
        { "brand_id": "BRAND_FAMILYMART", "brand_name": "全家便利商店" }
      ],
      "created_at": "2027-01-01T00:00:00+08:00"
    },
    {
      "request_id": "REQ_20261020_00002",
      "type": "change_brand",
      "added_brands": [
        { "brand_id": "BRAND_COSMED", "brand_name": "康是美" }
      ],
      "removed_brands": [
        { "brand_id": "BRAND_FAMILYMART", "brand_name": "全家便利商店" }
      ],
      "created_at": "2026-10-20T11:00:00+08:00"
    },
    {
      "request_id": "REQ_20261015_00001",
      "type": "pause",
      "created_at": "2026-10-15T20:30:00+08:00"
    },
    {
      "request_id": "REQ_20261001_00001",
      "type": "initial_selection",
      "selected_brands": [
        { "brand_id": "BRAND_FAMILYMART", "brand_name": "全家便利商店" }
      ],
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
| items | Array | 該用戶過去 1 年內的設定異動紀錄，每筆對應一次操作 |

### items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| request_id | String | 操作批次識別碼 |
| type | String | 操作類型：`initial_selection` \| `change_brand` \| `pause` \| `resume` \| `system_clear_brands` |
| added_brands | Array \| 省略 | 本次新增的品牌清單；**僅 `change_brand` 類型回傳** |
| removed_brands | Array \| 省略 | 本次移除的品牌清單；**僅 `change_brand` 類型回傳** |
| selected_brands | Array \| 省略 | 首次選牌的品牌清單；**僅 `initial_selection` 類型回傳** |
| cleared_brands | Array \| 省略 | 被系統清空的品牌清單；**僅 `system_clear_brands` 類型回傳** |
| created_at | String | 操作發生時間（UTC+8 ISO 8601） |

### brand 子物件（`added_brands` / `removed_brands` / `selected_brands` / `cleared_brands` 內每項）

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brand_id | String | 品牌 ID |
| brand_name | String | 品牌名稱（記錄當時快照，可能為已失效品牌） |

### 邏輯說明
- 依 `created_at` 由新到舊排序，僅回傳過去 1 年內紀錄
- 每筆 `items` 對應一次完整操作（一個 `request_id`），不再以個別品牌事件展開
- 品牌資訊於寫入時快照並存入 DB，查詢時直接回傳，以支援已失效品牌的顯示（前端無法透過 `get_current_rotation` 取得失效品牌資料）
- `change_brand`：代表一般品牌更換操作，展開 `added_brands` 與 `removed_brands`
- `initial_selection`：首次選牌，展開 `selected_brands`
- `pause` / `resume`：服務暫停／重啟，不展開品牌子項
- `system_clear_brands`：系統 lazy cleanup 清空舊檔期選擇，展開 `cleared_brands`；`created_at` 為舊 rotation 的 `end_time`
- 無任何異動紀錄時，回傳 `items: []`，不報錯

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
