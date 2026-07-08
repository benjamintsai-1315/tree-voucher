---
title: API Spec - get_member_orders
permalink: /api-specs/get-member-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
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
讓樹享券平台前台端以 API Key 依 member_id 取得該會員的訂單列表，支援分頁，固定以 `transaction_time DESC` 排序，供會員瀏覽歷史折抵紀錄。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受發卡主機的 API Key
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
      "order_id": "ORD_20261001_00001",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店"
      },
      "cash_amount": 620,
      "card_last_four_digits": "1234",
      "discount_amount": 141,
      "order_status": "completed",
      "transaction_time": "2026-10-01T14:28:00+08:00",
      "finalized_at": "2026-10-03T10:00:00+08:00",
      "created_at": "2026-10-01T14:30:00+08:00"
    },
    {
      "order_id": "ORD_20261002_00005",
      "brand": {
        "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
        "name": "全家便利商店"
      },
      "cash_amount": 300,
      "card_last_four_digits": "5678",
      "discount_amount": 21,
      "order_status": "waiting_finalization",
      "transaction_time": "2026-10-02T09:08:00+08:00",
      "finalized_at": null,
      "created_at": "2026-10-02T09:10:00+08:00"
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
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| discount_amount | Integer | 本次實際折抵總金額（元） |
| order_status | String | 訂單當前狀態，取自 `order.status` 六態；本會員列表**剔除 `failed`**，實際僅出現 `waiting_finalization` \| `completed` \| `cancelled` |
| transaction_time | String | 發卡主機傳入的刷卡交易時間（UTC+8 ISO 8601）；列表依此欄位排序（DESC） |
| finalized_at | String \| null | 訂單終結時間；未終結（`waiting_finalization`）時為 `null`，`completed` / `cancelled` 時為終結時間 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

### brand

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼（ULID） |
| name | String | 品牌名稱 |

### 邏輯說明
- 列表為摘要資訊，不含 `coupons_used` 明細與 `events` 歷程；前台端不另提供單筆完整明細查詢
- **`order.status = failed` 的訂單（`create_order` 清算後折抵為 0）不列入本列表**；清算中的暫態（`pending` / `processing`）亦不會出現於已成立的訂單列表
- `items` 內的 `card_last_four_digits` 為建單時由發卡主機提供，供前台端在訂單列表顯示卡號辨識資訊
- 固定以 `transaction_time DESC` 排序

## 400 錯誤回傳（TYPE: MESSAGE）
1. member_id 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
