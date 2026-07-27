---
title: API Spec - get_coupons
permalink: /api-specs/get-coupons/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-27 | 補註 `status`：`create_order` 清算過程中 DB 可能存在內部中間態 `consuming`，本 API 一律顯示為 `consumed`，不對前端揭露 |
| 2026-07-24 | `campaign_name` 補註為 coupon 建立時的快照值（非即時 join campaign 表），campaign 事後改名不會回溯變動已發行券的顯示名稱 |
| 2026-07-23 | Response 陣列欄位由 `coupons` 更名為 `items`；Sample JSON、使用情境、邏輯說明同步修正 |
| 2026-07-23 | `status` 查詢參數由可複選 `status[]` 改回單選 `status`，enum 改為 `unsettled`／`available`／`consumed`／`settled`／`expired` 五選一；`unsettled` 為 API 查詢層級的別名（等同 `available`+`consumed`），非 coupon 狀態機的一員，不會出現在 response 的 `status` 欄位 |
| 2026-07-23 | `status[]` 查詢參數新增 `unsettled` 別名值，等同 `available`+`consumed`，供前端「待折抵」列表查詢時免帶兩個值；`unsettled` 僅為 API 查詢層級的翻譯，不進入 coupon 狀態機、不會出現在 response 的 `status` 欄位 |
| 2026-07-22 | 效能討論定案：前端改以三個獨立列表呈現（待折抵 `available`+`consumed`／已折抵 `settled`／已過期 `expired`），取代原本兩頁籤（待折抵／紀錄）設計；不採用先前討論的「三態收斂（available/used/expired）」方案，狀態 enum 與排序規則維持四態不變；補充說明 `settled`／`expired` 排序欄位不同，前端不應合併查詢 |
| 2026-07-21 | coupon 狀態 enum 統一改為小寫（`available`/`consumed`/`settled`/`expired`），取代先前大寫值，與 DB 欄位一致，API 不做大小寫轉換；`status[]` 查詢參數、response `status` 欄位、排序規則說明皆同步修正 |
| 2026-07-14 | 補上 `updated_at`：`SETTLED` bucket 排序依此欄位（finalize 時間），但先前 response 未實際回傳此欄位，說明與資料不一致，此次補齊 |
| 2026-07-14 | 修正說明不清：`id`（券識別碼）型別補上 ULID 註記；sample 的 `CPN_001`/`CPN_002` 佔位字串改為 ULID 格式，避免誤導實際格式 |
| 2026-07-13 | Response 精簡化：`coupons[]` 移除列表畫面不需要的 `brand`、`redeem_points`、`discount_rate`、`max_redemptions_per_order`、`created_at`，`campaign` 巢狀物件改為扁平 `campaign_name`；同時調整同一狀態 bucket 排序規則：`AVAILABLE`/`CONSUMED`/`EXPIRED` 改為 `expired_at DESC`、`id ASC`，`SETTLED` 改依 `updated_at DESC`（finalize 時間）、`id ASC` |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `status` 改為可複選（`status[]`，repeatable query param） |
| 2026-07-02 | `brand_*` 欄位改為巢狀 `brand: {id, name, logo}`；`campaign_*` 欄位改為巢狀 `campaign: {id, name, type}` |
| 2026-07-01 | `brand_id` 限制由 UUID 改為 ULID；`brand_id`/`campaign_id` 範例值改為 ULID 格式 |
| 2026-06-23 | 由 `get_coupon_wallet` 改名為 `get_coupons`；端點更新為 `/coupon/get_coupons` |
| 2026-06-16 | 欄位去除多餘 prefix：`coupon_id` → `id`；coupon 快照欄位 `coupon_min_order_amount/redeem_points/discount_amount` → `min_order_amount/redeem_points/discount_amount`；`PROCESSING/COMPLETED` status 值同步改為 `CONSUMED/SETTLED` |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled`；更新預設排序 bucket 說明 |
| 2026-06-15 | 每張券新增 `campaign_type`（`auto`\|`manual`）與 `discount_rate` 計算欄位 |
| 2026-06-12 | `user_id` → `member_id`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: get_coupons

## 功能說明
讓樹配券平台前台端以 API Key 依 `member_id` 查詢該用戶的券列表，支援依 `brand_id` 與單一 `status` 篩選，供前端呈現特定品牌下的可用券、處理中券與歷史券。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - `brand_id` 若有帶入，必須存在於神坊系統中
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境
前台端由品牌卡片（`get_coupon_wallet`）進入後，帶入 `member_id` 與 `brand_id` 查詢該品牌下的券列表。前端以三個列表呈現：**待折抵**（`status=unsettled`，等同 `available`+`consumed`）、**已折抵**（`status=settled`）、**已過期**（`status=expired`），各自獨立查詢、獨立分頁，不合併呈現。

若使用者在該品牌目前沒有任何券，回傳 `items: []`，不視為錯誤。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_coupons`
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
| page | integer | FALSE | FALSE | 1 | > 0 |
| limit | integer | FALSE | FALSE | 20 | > 0 |
| brand_id | string | FALSE | FALSE | ❎ | ULID |
| status | string | FALSE | FALSE | ❎ | 單選，僅接受 `unsettled` \| `available` \| `consumed` \| `settled` \| `expired` 其中一個值；不帶表示回傳全部狀態。`unsettled` 為 API 查詢層級的別名，等同同時查詢 `available` + `consumed`，**非** coupon 狀態機的實際狀態值，不會出現在 response 的 `status` 欄位 |

# Response
## Sample（JSON）

```json
{
  "page": 1,
  "limit": 20,
  "total": 3,
  "items": [
    {
      "id": "01HZYA1B2C3D4E5F6G7H8J9K0M",
      "status": "available",
      "campaign_name": "滿100折21",
      "min_order_amount": 100,
      "discount_amount": 21,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "updated_at": "2026-10-01T09:00:00.000+08:00"
    },
    {
      "id": "01HZYB2C3D4E5F6G7H8J9K0MNP",
      "status": "settled",
      "campaign_name": "滿100折21",
      "min_order_amount": 100,
      "discount_amount": 21,
      "expired_at": "2026-10-31T23:59:59.999+08:00",
      "updated_at": "2026-10-05T10:00:00.000+08:00"
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
| items | Array | 該用戶符合篩選條件的券列表 |

### items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 券識別碼（ULID） |
| status | String | 券狀態：`available` \| `consumed` \| `settled` \| `expired`。DB 於 `create_order` 清算過程中可能存在內部中間態 `consuming`（2026-07-27 起，詳見 CLAUDE.md「Coupon 狀態 enum」），本 API 一律將其顯示為 `consumed`，不對前端揭露 `consuming` |
| campaign_name | String | 該券所屬 campaign 名稱（coupon 建立時的快照，非即時 join campaign 表；campaign 事後改名不影響已發行券的顯示名稱） |
| min_order_amount | Integer | 該券對應的消費門檻金額（元） |
| discount_amount | Integer | 該券折抵金額（元） |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| updated_at | String | 該券最後更新時間（UTC+8 ISO 8601，毫秒精度）；狀態轉換時更新（如 `batch_finalize_orders` 核銷為 `settled` 的 finalize 時間）；`settled` bucket 依此欄位排序 |

### 邏輯說明
- `status` 為單選參數，僅能帶一個值；若帶入，僅回傳該狀態的券
- `status=unsettled` 為 API 查詢層級的別名，接收後在 API 內部展開為 `available` + `consumed` 兩個 DB 狀態值再查詢；`unsettled` 僅存在於這支 API 的查詢參數翻譯層，不是 coupon 狀態機（`available`/`consumed`/`settled`/`expired`）的一員，DB 欄位與 response 的 `status` 不會有此值
- 若帶 `brand_id`，僅回傳該品牌底下的券
- 同一狀態 bucket 內排序：
  - `available`、`consumed` bucket 依 `expired_at DESC`、`id ASC` 排序
  - `settled` bucket 依 `updated_at DESC`（finalize 的時間）、`id ASC` 排序
  - `expired` bucket 依 `expired_at DESC`、`id ASC` 排序
- 無任何符合條件的券時，回傳 `items: []`，不報錯
- 本 API 不回傳訂單關聯欄位，例如 `order_id`
- 本 API 回傳精簡化券資訊，供列表畫面使用；不含 `brand`（已由 `brand_id` 篩選帶入）、`redeem_points`、`discount_rate`、`max_redemptions_per_order`、`created_at`。如需完整詳情請呼叫 `get_coupon_detail`
- `updated_at` 為排序鍵之一（`settled` bucket 依此排序），故納入 response 回傳，避免排序依據的欄位卻無法讓前端查驗
- 前端固定以三個獨立查詢對應三個列表（見上方使用情境）：`status=unsettled`（內部等同 `available`＋`consumed`，兩者排序欄位相同，皆為 `expired_at`，故可安全合併查詢）、`status=settled`（`updated_at`）、`status=expired`（`expired_at`）；`settled`／`expired` 排序欄位不同，各自單選查詢即可維持單一排序鍵直接命中索引，不需額外處理

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
3. `brand_id` 不存在：`BRAND_NOT_FOUND`