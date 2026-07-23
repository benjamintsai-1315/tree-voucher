---
title: API Spec - get_member_orders
permalink: /api-specs/get-member-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-23 | `coupon_usage_summary` 結構調整：分組鍵由 `campaign_name` + `is_new_issued` 改為 `campaign_id`（新增此欄位），同一 campaign 的新／舊券使用合併為一筆，透過巢狀 `coupon_usage.new_issued` / `coupon_usage.existing` 呈現；點數消耗（`used_points`）下放至各類別，`discount_amount` 更名為 `total_discount_amount`；`point_used`（訂單層級）明訂為各 campaign `new_issued.used_points` 的加總，屬衍生欄位非獨立來源 |
| 2026-07-21 | 效能討論定案：`coupon_usage_summary`／`point_used` 改為讀取 `create_order` 建單當下寫入的快照，不再於本 API 查詢當下即時 JOIN／GROUP BY 聚合，降低列表查詢運算成本並避免大量用券訂單的 response 過大；response 欄位結構不變 |
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
        {
          "campaign_id": "01HZYE1F2G3H4J5K6M7N8P9Q0R",
          "campaign_name": "樹配券 $20",
          "coupon_usage": {
            "new_issued": {
              "quantity": 1,
              "total_discount_amount": 20,
              "used_points": { "tree_points": 0, "cub_points": 20 }
            },
            "existing": {
              "quantity": 0,
              "total_discount_amount": 0,
              "used_points": { "tree_points": 0, "cub_points": 0 }
            }
          }
        }
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
        {
          "campaign_id": "01HZYE2G3H4J5K6M7N8P9Q0R1S",
          "campaign_name": "樹配券 $30",
          "coupon_usage": {
            "new_issued": {
              "quantity": 0,
              "total_discount_amount": 0,
              "used_points": { "tree_points": 0, "cub_points": 0 }
            },
            "existing": {
              "quantity": 3,
              "total_discount_amount": 90,
              "used_points": { "tree_points": 0, "cub_points": 0 }
            }
          }
        },
        {
          "campaign_id": "01HZYE3H4J5K6M7N8P9Q0R1S2T",
          "campaign_name": "樹配券 $24",
          "coupon_usage": {
            "new_issued": {
              "quantity": 3,
              "total_discount_amount": 72,
              "used_points": { "tree_points": 30, "cub_points": 30 }
            },
            "existing": {
              "quantity": 0,
              "total_discount_amount": 0,
              "used_points": { "tree_points": 0, "cub_points": 0 }
            }
          }
        }
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
        {
          "campaign_id": "01HZYE3H4J5K6M7N8P9Q0R1S2T",
          "campaign_name": "樹配券 $24",
          "coupon_usage": {
            "new_issued": {
              "quantity": 3,
              "total_discount_amount": 72,
              "used_points": { "tree_points": 30, "cub_points": 30 }
            },
            "existing": {
              "quantity": 0,
              "total_discount_amount": 0,
              "used_points": { "tree_points": 0, "cub_points": 0 }
            }
          }
        }
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
| coupon_usage_summary | Array | 本次訂單所用券，依 `campaign_id` 分組聚合的使用摘要（拆分新發券／既有券兩類），見下表 |
| point_used | Object | 本次訂單**新發券**消耗的點數總計；等於 `coupon_usage_summary[].coupon_usage.new_issued.used_points` 加總（各 campaign 新發券點數消耗加總，沿用既有券不消耗點數），見下表 |
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
| campaign_id | String | 該組券所屬 campaign 識別碼（ULID） |
| campaign_name | String | 該組券所屬 campaign 名稱（如「樹配券 $30」） |
| coupon_usage | Object | 依券來源拆分的使用明細，見下表 |

### coupon_usage_summary.coupon_usage

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| new_issued | Object | 本次訂單即時發行的新券使用明細，見下表 |
| existing | Object | 本次訂單使用的既有（舊）券使用明細，見下表 |

`new_issued` 與 `existing` 皆為同一結構：

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| quantity | Integer | 該類別使用的券張數；該 campaign 未使用此類別券時為 `0` |
| total_discount_amount | Integer | 該類別小計折抵金額（元）；未使用時為 `0`；訂單取消（`order_status = cancelled`）時仍為原始計算值，前端應依 `order_status` 顯示為「已退回券匣」，不直接呈現金額 |
| used_points | Object | 該類別消耗的點數，見下表；`existing` 恆為 `0`（既有券不消耗點數） |

### coupon_usage_summary.coupon_usage.{new_issued\|existing}.used_points

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| tree_points | Integer | 該類別消耗的小樹點(生活) |
| cub_points | Integer | 該類別消耗的小樹點(信用卡) |

### point_used

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| tree_points | Integer | 本次新發券消耗的小樹點(生活)；若本次全數使用既有券則為 `0` |
| cub_points | Integer | 本次新發券消耗的小樹點(信用卡)；若本次全數使用既有券則為 `0` |

### 邏輯說明
- 列表為摘要資訊，`coupon_usage_summary` 為依 `campaign_id` 分組的聚合統計，非逐張券明細；本 API 仍不含逐張 `coupons_used` 明細與 `events` 歷程，前台端不另提供單筆完整明細查詢
- `coupon_usage_summary`／`point_used` 為 **`create_order` 建單當下即計算完成並寫入 order 記錄的快照**（詳見 `create_order.md`「`get_member_orders` 用券摘要快照」段落），本 API 直接讀取該快照回傳，不於查詢當下即時 JOIN／GROUP BY 聚合——藉此降低列表查詢的即時運算成本；快照寫入後不隨後續 coupon 狀態變化（如轉為 `settled`）而更動
- 同一 campaign 若同時有新券與舊券於本次訂單被使用，合併為同一筆 `coupon_usage_summary` row（依 `campaign_id` 分組），透過 `coupon_usage.new_issued` / `coupon_usage.existing` 兩個子物件分別呈現各自張數、金額與點數消耗，不再依新舊券拆成兩筆
- 某 campaign 若本次僅使用其中一類券（例如全部為既有券），`coupon_usage.new_issued` 或 `coupon_usage.existing` 仍完整輸出，`quantity`／`total_discount_amount`／`used_points` 皆為 `0`，非省略該子物件
- `point_used` 與各 campaign 的 `coupon_usage.new_issued.used_points` 為同一份快照的不同呈現粒度：`point_used` = Σ 所有 campaign 的 `coupon_usage.new_issued.used_points`，非各自獨立來源，保留於訂單層級供前端不需自行迭代加總即可顯示點數總計
- **`order.status = error` 的訂單（`create_order` 清算後折抵為 0）不列入本列表**；清算中的暫態（`pending`）亦不會出現於已成立的訂單列表
- `items` 內的 `card_last_four_digits`、`store_name` 為建單時由發卡主機提供，供前台端在訂單列表顯示辨識資訊
- 訂單取消時，`discount_amount` 與 `coupon_usage_summary[].coupon_usage.{new_issued|existing}.total_discount_amount` 皆維持既有欄位語意（前者歸零、後者為原始計算值），前端純依 `order_status = cancelled` 判斷顯示邏輯，不需額外欄位
- 固定以 `transaction_time DESC` 排序

## 400 錯誤回傳（TYPE: MESSAGE）
1. member_id 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
