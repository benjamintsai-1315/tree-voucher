---
title: API Spec - get_member_settings_change_logs
permalink: /api-specs/get-member-settings-change-logs/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-25 | type enum 全面改名：`change_brand` → `change_selected_brands`、`pause` → `disable_auto_redeem`、`resume` → `enable_auto_redeem`；移除 `initial_selection`（首次選牌統一歸類為 `change_selected_brands`）；response 結構改為統一 `data.before_brands` / `data.after_brands`；移除 `request_id`；`limit` 上限改為 20 |
| 2026-06-24 | `limit` 上限改為 20 筆；各 brand array 統一改為 data dict |
| 2026-06-22 | 由 `get_member_brand_change_logs` 更名；endpoint 改為 `/coupon/get_member_settings_change_logs` |
| 2026-06-15 | 回傳結構改為 request 粒度（一筆 = 一次操作） |
| 2026-06-12 | 由 `get_user_brand_change_logs` 更名 |

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

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 20 | 1~20；超過 20 回 422 |

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
        "before_brands": [
          { "id": "BRAND_FAMILYMART", "name": "全家便利商店" }
        ],
        "after_brands": []
      },
      "created_at": "2027-01-01T00:00:00+08:00"
    },
    {
      "type": "change_selected_brands",
      "data": {
        "before_brands": [],
        "after_brands": [
          { "id": "BRAND_FAMILYMART", "name": "全家便利商店" }
        ]
      },
      "created_at": "2026-10-20T11:00:00+08:00"
    },
    {
      "type": "enable_auto_redeem",
      "data": null,
      "created_at": "2026-10-15T20:30:00+08:00"
    },
    {
      "type": "change_selected_brands",
      "data": {
        "before_brands": [
          { "id": "BRAND_FAMILYMART", "name": "全家便利商店" }
        ],
        "after_brands": [
          { "id": "BRAND_COSMED", "name": "康是美" }
        ]
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
| limit | Integer | 每頁筆數，1 ≤ limit ≤ 20 |
| total | Integer | 符合條件的總筆數 |
| items | Array | 該用戶過去 1 年內的設定異動紀錄 |

### items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| type | String | 操作類型：`change_selected_brands` \| `disable_auto_redeem` \| `enable_auto_redeem` \| `system_clear_brands` |
| data | Object \| null | 品牌異動明細；`change_selected_brands` / `system_clear_brands` 回傳；`disable_auto_redeem` / `enable_auto_redeem` 為 `null` |
| created_at | String | 操作發生時間（UTC+8 ISO 8601） |

### data（當 type = `change_selected_brands` 或 `system_clear_brands`）

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| before_brands | Array | 異動前的品牌清單；首次選牌時為 `[]` |
| after_brands | Array | 異動後的品牌清單；系統清空時為 `[]` |

### brand 子物件（`before_brands` / `after_brands` 內每項）

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌 ID |
| name | String | 品牌名稱（反查當下 brand_name，可能為已失效品牌） |

## 邏輯說明
- 依 `created_at` 由新到舊排序，僅回傳過去 1 年內紀錄
- `change_selected_brands`：涵蓋首次選牌與後續品牌更換，統一以此 type 表示；`before_brands` 為異動前清單，`after_brands` 為異動後清單
- `disable_auto_redeem` / `enable_auto_redeem`：服務暫停／重啟，`data: null`
- `system_clear_brands`：系統 lazy cleanup 清空舊檔期，`before_brands` 為被清空的品牌、`after_brands` 為 `[]`；`created_at` 為舊 rotation 的 `end_time`
- `name` 欄位：取 brands 表最新名稱（以支援已失效品牌的顯示）
- 搜尋範圍內無任何異動紀錄時（含頁數超過 total），回傳 `items: []`，不報錯

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
