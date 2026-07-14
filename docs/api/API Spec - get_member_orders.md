---
title: API Spec - get_member_orders
permalink: /api-specs/get-member-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-14 | `coupon_usage_summary[]` 新增 `is_new_issued`（是否為本次訂單即時發行的新券），供前端區分新／舊券做差異顯示；分組鍵同步調整為 `campaign_name` + `is_new_issued`（同一 campaign 若同時有新券與舊券，分兩組回傳） |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`、`failed` 更名為 `error`；本會員列表可見狀態改為 `processing` \| `completed` \| `cancelled` |
| 2026-07-13 | 補齊前端列表畫面所需欄位：新增 `store_name`（`create_order` 已有此快照欄位，此前漏未於本 API 回傳）；新增 `coupon_usage_summary[]`（依 campaign 分組聚合的券使用摘要，非逐張明細）與 `point_used`（本次新發券消耗點數） |
| 2026-07-08 | 前台端 `get_order` 廢除後，明訂本 API 不提供單筆完整明細（`coupons_used`/`events`）查詢；移除原「呼叫 `get_order`」導引 |
| 2026-07-08 | `order_status` 對齊 `order.status` 六態（小寫），本會員列表剔除 `failed`、暫態不出現；`finalized_at` 說明改為終結（`completed`/`cancelled`）前為 null |
| 2026-07-02 | 排序改為 `transaction_time DESC`；新增 `transaction_time` response 欄位（發卡主機傳入的刷卡交易時間，供前端顯示用） |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `brand` 欄位說明獨立為子表格；移除 `sort_by`/`sort_order` 參數，固定以 `created_at DESC` 排序 |
| 2026-07-02 | `brand_id`、`brand_name` 改為巢狀物件 `brand: { id, name }` |
| 2026-07-01 | `brand_id` 範例值改為 ULID 格式 |
| 2026-06-12 | 由 `get_user_orders` 更名；`user_id` → `member_id`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND`；endpoint 改為 `/coupon/get_member_orders` |

# API: get_member_orders

## 功能說明
讓樹配券平台前台端以 API Key 依 member_id 取得該會員的訂單列表，支援分頁，固定以 `transaction_time DESC` 排序，供會員瀏覽歷史折抵紀錄。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權，不接受發卡主機的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境
前台端帶入 `member_id` 取得該會員所有訂單的摘要列表。前台端不提供單筆訂單完整明細（`coupons_used` / `events` 歷程）查詢。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_member_orders`
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
  "total": 3,
  "items": [
    {
      "order_id": "ORD_20260920_00001",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店"
      },
      "store_name": "全家便利商店一土城行政店",
      "cash_amount": 600,
      "card_last_four_digits": "7284",
      "discount_amount": 20,
      "coupon_usage_summary": [
        { "campaign_name": "樹配券 $20", "is_new_issued": true, "discount_amount": 20, "quantity": 1 }
      ],
      "point_used": {
        "tree_points": 0,
        "cub_points": 20
      },
      "order_status": "processing",
      "transaction_time": "2026-09-20T23:59:59+08:00",
      "finalized_at": null,
      "created_at": "2026-09-20T23:59:59+08:00"
    },
    {
      "order_id": "ORD_20260919_00005",
      "brand": {
        "id": "01HZYC3D4E5F6G7H8J9K0MNPQR",
        "name": "POYA寶雅"
      },
      "store_name": "POYA寶雅 信義松壽店",
      "cash_amount": 600,
      "card_last_four_digits": "7284",
      "discount_amount": 162,
      "coupon_usage_summary": [
        { "campaign_name": "樹配券 $30", "is_new_issued": false, "discount_amount": 90, "quantity": 3 },
        { "campaign_name": "樹配券 $24", "is_new_issued": true, "discount_amount": 72, "quantity": 3 }
      ],
      "point_used": {
        "tree_points": 30,
        "cub_points": 30
      },
      "order_status": "completed",
      "transaction_time": "2026-09-19T23:59:59+08:00",
      "finalized_at": "2026-09-20T02:00:00+08:00",
      "created_at": "2026-09-19T23:59:59+08:00"
    },
    {
      "order_id": "ORD_20260917_00002",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店"
      },
      "store_name": "全家便利商店土城中源店",
      "cash_amount": 600,
      "card_last_four_digits": "7284",
      "discount_amount": 0,
      "coupon_usage_summary": [
        { "campaign_name": "樹配券 $24", "is_new_issued": true, "discount_amount": 72, "quantity": 3 }
      ],
      "point_used": {
        "tree_points": 30,
        "cub_points": 30
      },
      "order_status": "cancelled",
      "transaction_time": "2026-09-17T23:59:59+08:00",
      "finalized_at": "2026-09-18T02:00:00+08:00",
      "created_at": "2026-09-17T23:59:59+08:00"
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
| items | Array | 訂單摘要列表 |

### items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| brand | Object | 對應品牌資訊，見下表 |
| store_name | String | 刷卡門市名稱，`create_order` 建單時由發卡主機傳入的快照值，原樣呈現，不做任何品牌/門市對應轉換 |
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| discount_amount | Integer | 本次折抵總金額（元）；`order_status = processing` 時為清算當下計算之預計金額，`completed` 時為實際折抵金額，`cancelled` 時固定為 `0` |
| coupon_usage_summary | Array | 本次訂單所用券，依 `campaign_name` 分組聚合的使用摘要，見下表 |
| point_used | Object | 本次訂單**新發券**消耗的點數（僅新券產生點數消耗，沿用既有券不消耗點數），見下表 |
| order_status | String | 訂單當前狀態，取自 `order.status` 五態；本會員列表**剔除 `error`**，實際僅出現 `processing` \| `completed` \| `cancelled` |
| transaction_time | String | 發卡主機傳入的刷卡交易時間（UTC+8 ISO 8601）；列表依此欄位排序（DESC） |
| finalized_at | String \| null | 訂單終結時間；未終結（`processing`）時為 `null`，`completed` / `cancelled` 時為終結時間 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

### brand

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼（ULID） |
| name | String | 品牌名稱 |

### coupon_usage_summary

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| campaign_name | String | 該組券所屬 campaign 名稱（如「樹配券 $30」） |
| is_new_issued | Boolean | `true`：本次訂單即時發行的新券（新券段）；`false`：本次訂單之前已存在的舊券（既有券段所用），供前端區分新／舊券做差異顯示 |
| discount_amount | Integer | 該組券小計折抵金額（元）；訂單取消（`order_status = cancelled`）時仍為原始計算值，前端應依 `order_status` 顯示為「已退回券匣」，不直接呈現金額 |
| quantity | Integer | 該組使用的券張數 |

### point_used

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| tree_points | Integer | 本次新發券消耗的小樹點(生活)；若本次全數使用既有券則為 `0` |
| cub_points | Integer | 本次新發券消耗的小樹點(信用卡)；若本次全數使用既有券則為 `0` |

### 邏輯說明
- 列表為摘要資訊，`coupon_usage_summary` 為依 `campaign_name` + `is_new_issued` 分組的聚合統計，非逐張券明細；本 API 仍不含逐張 `coupons_used` 明細與 `events` 歷程，前台端不另提供單筆完整明細查詢
- 同一 campaign 若同時有新券與舊券於本次訂單被使用，分為兩組回傳（`is_new_issued` 不同即不合併），確保前端能正確做新／舊券差異顯示
- **`order.status = error` 的訂單（`create_order` 清算後折抵為 0）不列入本列表**；清算中的暫態（`pending`）亦不會出現於已成立的訂單列表
- `items` 內的 `card_last_four_digits`、`store_name` 為建單時由發卡主機提供，供前台端在訂單列表顯示辨識資訊
- 訂單取消時，`discount_amount` 與 `coupon_usage_summary[].discount_amount` 皆維持既有欄位語意（前者歸零、後者為原始計算值），前端純依 `order_status = cancelled` 判斷顯示邏輯，不需額外欄位
- 固定以 `transaction_time DESC` 排序

## 400 錯誤回傳（TYPE: MESSAGE）
1. member_id 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
