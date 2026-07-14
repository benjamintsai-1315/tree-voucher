---
title: API Spec - get_coupon_detail
permalink: /api-specs/get-coupon-detail/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-14 | 修正說明不清：`id`（券識別碼）型別補上 ULID 註記；sample 的 `CPN_001` 佔位字串改為 ULID 格式，避免誤導實際格式 |
| 2026-07-14 | 新增 `tree_points`/`cub_points`：`redeem_points` 僅為合計，未拆分兩種點數組成，資訊不足；補上兩種點數明細，資料來源與 `create_order` 對帳一致（`treelife_use_point_log`） |
| 2026-07-13 | 明確定義 `created_at` 即為券「有效期間」之起始時間，並補齊毫秒精度，與 `expired_at` 一致 |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `brand_*` 欄位改為巢狀 `brand: {id, name, logo}`；`campaign_*` 欄位改為巢狀 `campaign: {id, name, type}` |
| 2026-07-01 | `brand_id`/`campaign_id` 範例值改為 ULID 格式，並於 response items 補上 ULID 型別註記 |
| 2026-06-23 | 初版 |

# API: get_coupon_detail

## 功能說明
查詢單張券的完整詳情，包含狀態、效期、折抵規則，以及當初兌換此券所花費的點數。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - `coupon_id` 必須存在且屬於該 `member_id`
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境
前台端由券列表（`get_coupons`）點入單張券後，顯示該券的完整詳情。`redeem_points` 即為當初兌換此券所花費的點數合計（coupon 建立時的快照），並拆分為 `tree_points`（小樹點生活）與 `cub_points`（小樹點信用卡）兩種點數組成。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_coupon_detail`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | UUID |
| coupon_id | string | TRUE | FALSE | ❎ | ULID |

# Response
## Sample（JSON）

```json
{
  "id": "01HZYA1B2C3D4E5F6G7H8J9K0M",
  "status": "AVAILABLE",
  "brand": {
    "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
    "name": "全家便利商店",
    "logo": "https://cdn.example.com/logos/familymart.png"
  },
  "campaign": {
    "id": "01HZY5Q8WP5G7N9R2T4V6X8ZBD",
    "name": "滿100折21",
    "type": "auto"
  },
  "min_order_amount": 100,
  "redeem_points": 20,
  "tree_points": 8,
  "cub_points": 12,
  "discount_amount": 21,
  "discount_rate": 1.05,
  "max_redemptions_per_order": 3,
  "expired_at": "2026-10-31T23:59:59.999+08:00",
  "created_at": "2026-10-01T09:00:00.000+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 券識別碼（ULID） |
| status | String | 券狀態：`AVAILABLE` \| `CONSUMED` \| `SETTLED` \| `EXPIRED` |
| brand | Object | 對應品牌資訊，見下表 |
| campaign | Object | 該券所屬 campaign 資訊，見下表 |
| min_order_amount | Integer | 該券對應的消費門檻金額（元） |
| redeem_points | Integer | 兌換此券所花費的點數合計（coupon 建立時的快照）；等於 `tree_points + cub_points` |
| tree_points | Integer | 兌換此券所使用的小樹點(生活)數量（coupon 建立時的快照） |
| cub_points | Integer | 兌換此券所使用的小樹點(信用卡)數量（coupon 建立時的快照） |
| discount_amount | Integer | 該券折抵金額（元） |
| discount_rate | Float | 每點折抵金額比率，`round(discount_amount / redeem_points, 2)`，純計算欄位 |
| max_redemptions_per_order | Integer | 該券所屬 campaign 定義的單筆交易 active campaign 券使用張數上限 |
| expired_at | String | 該券固定到期時間，即有效期間迄日（UTC+8 ISO 8601，毫秒精度） |
| created_at | String | 該券建立時間，即有效期間起始時間（UTC+8 ISO 8601，毫秒精度） |

### brand

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼（ULID） |
| name | String | 品牌名稱 |
| logo | String | 品牌 logo 圖片 URL |

### campaign

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | Campaign 識別碼（ULID） |
| name | String | Campaign 名稱 |
| type | String | Campaign 類型：`auto`（系統自動兌換）\| `manual`（用戶手動兌換） |

### 邏輯說明
- `coupon_id` 必須屬於該 `member_id`，否則回傳 `COUPON_NOT_FOUND`
- `redeem_points`、`tree_points`、`cub_points` 皆為 coupon 建立時的快照值，不隨 campaign 規則變動；`tree_points`/`cub_points` 取自該券發行時寫入 `treelife_use_point_log` 的 `used_tree_points`/`used_cub_points`
- `created_at` 即該券有效期間之起始時間，與 `expired_at` 共同構成完整的有效期間起迄，兩者時間精度一致（毫秒）
- 本 API 不回傳訂單關聯欄位，例如 `order_id`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
3. `coupon_id` 不存在或不屬於該 `member_id`：`COUPON_NOT_FOUND`
