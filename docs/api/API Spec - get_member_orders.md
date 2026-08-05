---
title: API Spec - get_member_orders
permalink: /api-specs/get-member-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-05 | `coupon_usage_summary[]` 欄位更名：`campaign_discount_amount` → `coupon_discount_amount`（review 後定案，語意上此為 coupon 建立時的快照值而非 campaign 當下設定，改用 `coupon_` 前綴避免誤解為即時反查 campaign 表）；分組鍵、Sample、欄位說明同步更新 |
| 2026-07-29 | 全系統時間精度盤點：`finalized_at`／`created_at` 補註「毫秒精度」，Sample 補上 `.000` 精度；`transaction_time` 為發卡主機提供之原樣值，明訂不強制補齊毫秒，排除於本次盤點範圍外 |
| 2026-07-29 | `coupon_usage_summary[]` 新增 `campaign_discount_amount`（該 campaign 定義之單張券折抵金額，coupon 建立時快照）；`campaign_name` 範例值改為不含金額的泛用名稱（如「樹配券」），實際金額由 `campaign_discount_amount` 提供，前端自行組成顯示字串；分組鍵同步擴充為 `campaign_id`+`campaign_name`+`campaign_discount_amount`，避免同一 `campaign_id` 下不同折抵金額的批次被誤合併 |
| 2026-07-24 | 修正 `used_points` 子表格說明歧義：訂單層級 `used_points` 維持僅計新發券本次消耗（與主表格說明一致），既有券原始發行時的歷史點數**不**計入此欄位，改為註明其實際呈現位置（`coupon_usage_summary[].coupon_usage.existing.tree_points`/`cub_points`） |
| 2026-07-24（訂正） | 修正前次改動：改回**巢狀**設計（`coupon_usage_summary`，維持此欄位名，不更名為 `coupon_summary`，避免與 `create_order` 的物件型 `coupon_summary` 同名混淆），分組鍵為 `campaign_id`+`campaign_name`（修正改名情境下的正確性），同一組合下的新舊券合併為一筆、透過 `coupon_usage.new_issued`/`existing` 呈現；`tree_points`/`cub_points` 攤平為 `new_issued`/`existing` 內的同層欄位（不再額外包一層 `used_points`）；保留「`existing` 應呈現歷史點數、非恆零」的修正 |
| 2026-07-24 | 改回攤平陣列設計（取代上次的 `campaign_id` 巢狀合併方案）：`coupon_usage_summary` 更名為 `coupon_summary`（⚠️ 與 `create_order` 同名但結構不同，`create_order` 為物件、本 API 為陣列），每筆為 `campaign_id`+`campaign_name`+`is_new_issued` 組合的聚合列，只有實際使用的組合才輸出；`tree_points`/`cub_points` 攤平為同層欄位（取代巢狀 `used_points`），且修正先前「`existing` 恆為 0」的錯誤——`is_new_issued=false` 應呈現該券原始發行時的歷史點數（與 `create_order.coupon_summary.existing` 語意一致）；訂單層級 `discount_amount` 更名為 `total_discount_amount`；新增 `campaign_name` 為 coupon 快照欄位（可能因 campaign 改名而同一 `campaign_id` 對應不同名稱）的說明與範例 |
| 2026-07-23 | `coupon_usage_summary` 結構調整：分組鍵由 `campaign_name` + `is_new_issued` 改為 `campaign_id`（新增此欄位），同一 campaign 的新／舊券使用合併為一筆，透過巢狀 `coupon_usage.new_issued` / `coupon_usage.existing` 呈現；點數消耗（`used_points`）下放至各類別，`discount_amount` 更名為 `total_discount_amount`；`used_points`（訂單層級）明訂為各 campaign `new_issued.used_points` 的加總，屬衍生欄位非獨立來源 |
| 2026-07-21 | 效能討論定案：`coupon_usage_summary`／`used_points` 改為讀取 `create_order` 建單當下寫入的快照，不再於本 API 查詢當下即時 JOIN／GROUP BY 聚合，降低列表查詢運算成本並避免大量用券訂單的 response 過大；response 欄位結構不變 |
| 2026-07-14 | `coupon_usage_summary[]` 新增 `is_new_issued`（是否為本次訂單即時發行的新券），供前端區分新／舊券做差異顯示；分組鍵同步調整為 `campaign_name` + `is_new_issued`（同一 campaign 若同時有新券與舊券，分兩組回傳） |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`、`failed` 更名為 `error`；本會員列表可見狀態改為 `processing` \| `completed` \| `cancelled` |
| 2026-07-13 | 補齊前端列表畫面所需欄位：新增 `store_name`（`create_order` 已有此快照欄位，此前漏未於本 API 回傳）；新增 `coupon_usage_summary[]`（依 campaign 分組聚合的券使用摘要，非逐張明細）與 `used_points`（本次新發券消耗點數） |
| 2026-07-08 | 前台端 `get_order` 廢除後，明訂本 API 不提供單筆完整明細（`coupons_used`/`events`）查詢；移除原「呼叫 `get_order`」導引 |
| 2026-07-08 | `status` 對齊 `order.status` 六態（小寫），本會員列表剔除 `failed`、暫態不出現；`finalized_at` 說明改為終結（`completed`/`cancelled`）前為 null |
| 2026-07-02 | 排序改為 `transaction_time DESC`；新增 `transaction_time` response 欄位（發卡主機傳入的刷卡交易時間，供前端顯示用） |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `brand` 欄位說明獨立為子表格；移除 `sort_by`/`sort_order` 參數，固定以 `created_at DESC` 排序 |
| 2026-07-02 | `brand_id`、`brand_name` 改為巢狀物件 `brand: { id, name }` |
| 2026-07-01 | `brand_id` 範例值改為 ULID 格式 |
| 2026-06-12 | 由 `get_user_orders` 更名；`user_id` → `member_id`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND`；endpoint 改為 `/coupon/get_member_orders` |

# API: get_member_orders

## 功能說明
讓樹配券平台前台端以 API Key 依 member_id 取得該會員的訂單列表，支援分頁，固定以 `transaction_time DESC + id ASC` 排序，供會員瀏覽歷史折抵紀錄。

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
      "id": "ORD_20260920_00001",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店"
      },
      "store_name": "全家便利商店一土城行政店",
      "cash_amount": 600,
      "card_last_four_digits": "7284",
      "total_discount_amount": 20,
      "coupon_usage_summary": [
        {
          "campaign_id": "01HZYE1F2G3H4J5K6M7N8P9Q0R",
          "campaign_name": "樹配券",
          "coupon_discount_amount": 20,
          "coupon_usage": {
            "new_issued": {
              "quantity": 1,
              "total_discount_amount": 20,
              "tree_points": 0,
              "cub_points": 20
            },
            "existing": {
              "quantity": 0,
              "total_discount_amount": 0,
              "tree_points": 0,
              "cub_points": 0
            }
          }
        }
      ],
      "used_points": {
        "tree_points": 0,
        "cub_points": 20
      },
      "status": "processing",
      "transaction_time": "2026-09-20T23:59:59+08:00",
      "finalized_at": null,
      "created_at": "2026-09-20T23:59:59.000+08:00"
    },
    {
      "id": "ORD_20260919_00005",
      "brand": {
        "id": "01HZYC3D4E5F6G7H8J9K0MNPQR",
        "name": "POYA寶雅"
      },
      "store_name": "POYA寶雅 信義松壽店",
      "cash_amount": 600,
      "card_last_four_digits": "7284",
      "total_discount_amount": 162,
      "coupon_usage_summary": [
        {
          "campaign_id": "01HZYE2G3H4J5K6M7N8P9Q0R1S",
          "campaign_name": "樹配券",
          "coupon_discount_amount": 30,
          "coupon_usage": {
            "new_issued": {
              "quantity": 0,
              "total_discount_amount": 0,
              "tree_points": 0,
              "cub_points": 0
            },
            "existing": {
              "quantity": 3,
              "total_discount_amount": 90,
              "tree_points": 30,
              "cub_points": 30
            }
          }
        },
        {
          "campaign_id": "01HZYE3H4J5K6M7N8P9Q0R1S2T",
          "campaign_name": "樹配券",
          "coupon_discount_amount": 24,
          "coupon_usage": {
            "new_issued": {
              "quantity": 3,
              "total_discount_amount": 72,
              "tree_points": 30,
              "cub_points": 30
            },
            "existing": {
              "quantity": 0,
              "total_discount_amount": 0,
              "tree_points": 0,
              "cub_points": 0
            }
          }
        }
      ],
      "used_points": {
        "tree_points": 30,
        "cub_points": 30
      },
      "status": "completed",
      "transaction_time": "2026-09-19T23:59:59+08:00",
      "finalized_at": "2026-09-20T02:00:00.000+08:00",
      "created_at": "2026-09-19T23:59:59.000+08:00"
    },
    {
      "id": "ORD_20260917_00002",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店"
      },
      "store_name": "全家便利商店土城中源店",
      "cash_amount": 600,
      "card_last_four_digits": "7284",
      "total_discount_amount": 0,
      "coupon_usage_summary": [
        {
          "campaign_id": "01HZYE3H4J5K6M7N8P9Q0R1S2T",
          "campaign_name": "樹配券",
          "coupon_discount_amount": 24,
          "coupon_usage": {
            "new_issued": {
              "quantity": 3,
              "total_discount_amount": 72,
              "tree_points": 30,
              "cub_points": 30
            },
            "existing": {
              "quantity": 0,
              "total_discount_amount": 0,
              "tree_points": 0,
              "cub_points": 0
            }
          }
        },
        {
          "campaign_id": "01HZYE3H4J5K6M7N8P9Q0R1S2T",
          "campaign_name": "樹配券",
          "coupon_discount_amount": 22,
          "coupon_usage": {
            "new_issued": {
              "quantity": 0,
              "total_discount_amount": 0,
              "tree_points": 0,
              "cub_points": 0
            },
            "existing": {
              "quantity": 1,
              "total_discount_amount": 22,
              "tree_points": 10,
              "cub_points": 12
            }
          }
        }
      ],
      "used_points": {
        "tree_points": 30,
        "cub_points": 30
      },
      "status": "cancelled",
      "transaction_time": "2026-09-17T23:59:59+08:00",
      "finalized_at": "2026-09-18T02:00:00.000+08:00",
      "created_at": "2026-09-17T23:59:59.000+08:00"
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
| id | String | 訂單識別碼 |
| brand | Object | 對應品牌資訊，見下表 |
| store_name | String | 刷卡門市名稱，`create_order` 建單時由發卡主機傳入的快照值，原樣呈現，不做任何品牌/門市對應轉換 |
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| total_discount_amount | Integer | 本次折抵總金額（元）；`status = processing` 時為清算當下計算之預計金額，`completed` 時為實際折抵金額，`cancelled` 時固定為 `0` |
| coupon_usage_summary | Array | 本次訂單所用券，依 `campaign_id`+`campaign_name`+`coupon_discount_amount` 分組聚合的使用摘要（拆分新發券／既有券兩類），見下表 |
| used_points | Object | 本次訂單**新發券**消耗的點數總計；等於 `coupon_usage_summary[].coupon_usage.new_issued` 各筆的 `tree_points`/`cub_points` 加總（沿用既有券不消耗點數），見下表 |
| status | String | 訂單當前狀態，取自 `order.status` 五態；本會員列表**剔除 `error`**，實際僅出現 `processing` \| `completed` \| `cancelled` |
| transaction_time | String | 發卡主機傳入的刷卡交易時間（UTC+8 ISO 8601）；由發卡主機提供並原樣保存，精度依發卡主機提供之原始值，本系統不另外補齊毫秒；列表依此欄位排序（DESC） |
| finalized_at | String \| null | 訂單終結時間（UTC+8 ISO 8601，毫秒精度）；未終結（`processing`）時為 `null`，`completed` / `cancelled` 時為終結時間 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601，毫秒精度） |

### brand

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼（ULID） |
| name | String | 品牌名稱 |

### coupon_usage_summary

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| campaign_id | String | 該組券所屬 campaign 識別碼（ULID） |
| campaign_name | String | 該組券所屬 campaign 名稱（coupon 建立時的快照，不隨 campaign 事後異動回溯變動；若 campaign 曾經改名，同一 `campaign_id` 可能對應到不同的 `campaign_name`，見下方邏輯說明與 Sample 第 3 筆訂單範例）。範例值僅為泛用名稱（如「樹配券」），實際折抵金額由 `coupon_discount_amount` 另外提供，前端自行組成顯示字串（如「樹配券 20」） |
| coupon_discount_amount | Integer | 該 campaign 定義之單張券折抵金額（元），coupon 建立時的快照值，不隨 campaign 事後異動回溯變動；語意與 `get_coupon_detail` 的 `discount_amount` 一致，供前端與 `campaign_name` 組合顯示（如 `${campaign_name} ${coupon_discount_amount}`） |
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
| total_discount_amount | Integer | 該類別小計折抵金額（元）；未使用時為 `0`；訂單取消（`status = cancelled`）時仍為原始計算值，前端應依 `status` 顯示為「已退回券匣」，不直接呈現金額 |
| tree_points | Integer | `new_issued`：本次消耗的小樹點(生活)；`existing`：該券**原始發行時**所使用的小樹點(生活)（歷史值，非本次消耗，與 `create_order` 的 `coupon_summary.existing.tree_points` 語意一致）；未使用時為 `0` |
| cub_points | Integer | 同上，小樹點(信用卡)；未使用時為 `0` |

### used_points

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| tree_points | Integer | 本次新發券消耗的小樹點(生活)；若本次全數使用既有券則為 `0`。既有券本身於原始發行時的歷史點數組成**不計入此欄位**，改為依 campaign 分別呈現於 `coupon_usage_summary[].coupon_usage.existing.tree_points` |
| cub_points | Integer | 本次新發券消耗的小樹點(信用卡)；若本次全數使用既有券則為 `0`。既有券本身於原始發行時的歷史點數組成**不計入此欄位**，改為依 campaign 分別呈現於 `coupon_usage_summary[].coupon_usage.existing.cub_points` |

### 邏輯說明
- 列表為摘要資訊，`coupon_usage_summary` 為依 `campaign_id`+`campaign_name`+`coupon_discount_amount` 分組的聚合統計，非逐張券明細；本 API 仍不含逐張 `coupons_used` 明細與 `events` 歷程，前台端不另提供單筆完整明細查詢
- `coupon_usage_summary`／`used_points` 為 **`create_order` 建單當下即計算完成並寫入 order 記錄的快照**（詳見 `create_order.md`「`get_member_orders` 用券摘要快照」段落），本 API 直接讀取該快照回傳，不於查詢當下即時 JOIN／GROUP BY 聚合——藉此降低列表查詢的即時運算成本；快照寫入後不隨後續 coupon 狀態變化（如轉為 `settled`）而更動
- 同一 campaign（同 `campaign_id`+`campaign_name`+`coupon_discount_amount`）若同時有新券與舊券於本次訂單被使用，合併為同一筆 `coupon_usage_summary` row，透過 `coupon_usage.new_issued` / `coupon_usage.existing` 兩個子物件分別呈現各自張數、金額與點數，不再拆成兩筆——前端不需自行合併同 campaign 的多筆資料
- 某 campaign 若本次僅使用其中一類券（例如全部為既有券），`coupon_usage.new_issued` 或 `coupon_usage.existing` 仍完整輸出，`quantity`／`total_discount_amount`／`tree_points`／`cub_points` 皆為 `0`，非省略該子物件
- `campaign_name`／`coupon_discount_amount` 皆為 coupon 建立時凍結的快照值，不隨 campaign 事後異動（改名或調整折抵金額）回溯變動（見 PRD §二 Coupon 規則 1）。若 campaign 曾經異動，同一 `campaign_id` 底下不同批次發行的券可能對應不同的 `campaign_name`／`coupon_discount_amount`，會在 `coupon_usage_summary` 中各自成一筆（各自帶完整的 `coupon_usage.new_issued`/`existing`），不會合併也不會互相覆蓋——見 Sample 第 3 筆訂單範例：`campaign_id` 相同，但 `coupon_discount_amount` 分別為 `24`（本次新發券）與 `22`（沿用發行當下金額的舊券）而分屬兩筆
- `used_points` 與各筆 `coupon_usage.new_issued` 的 `tree_points`/`cub_points` 為同一份快照的不同呈現粒度：`used_points` = Σ 所有 campaign 的 `coupon_usage.new_issued.tree_points`/`cub_points`，非各自獨立來源，保留於訂單層級供前端不需自行迭代加總即可顯示點數總計
- **`order.status = error` 的訂單（`create_order` 清算後折抵為 0）不列入本列表**；清算中的暫態（`pending`）亦不會出現於已成立的訂單列表
- `items` 內的 `card_last_four_digits`、`store_name` 為建單時由發卡主機提供，供前台端在訂單列表顯示辨識資訊
- 訂單取消時，`total_discount_amount` 與 `coupon_usage_summary[].coupon_usage.{new_issued|existing}.total_discount_amount` 皆維持既有欄位語意（前者歸零、後者為原始計算值），前端純依 `status = cancelled` 判斷顯示邏輯，不需額外欄位
- 固定以 `transaction_time DESC` 排序，時間相同時以 `id ASC` 排序

## 400 錯誤回傳（TYPE: MESSAGE）
1. member_id 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
