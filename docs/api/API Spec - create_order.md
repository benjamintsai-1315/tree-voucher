---
title: API Spec - create_order
permalink: /api-specs/create-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-02 | 新增 `transaction_time` request 欄位（呈現用）；新增 `max_redemption_per_rotation` campaign 屬性與對應 quota 檢查；新增 rotation 邊界暫定說明 |
| 2026-07-01 | `brand_id` 限制改為 ULID |
| 2026-06-25 | 新增 `merchant_name` request 欄位（必填）；快照保存於 `orders` 表，供前台訂單列表顯示門市名稱 |
| 2026-06-25 | 放寬邊界檢查：`brand_id` 不再要求必須具備 active campaign；無 active campaign 時仍可使用既有 `available` 舊券；移除 `BRAND_HAS_NO_ACTIVE_CAMPAIGN` 錯誤碼 |
| 2026-06-25 | `cash_amount` 改名為 `order_amount`；移除 lazy cleanup 說明（見 PRD）；邏輯說明改為既有券清算 / 新券發行兩段結構 |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled` |
| 2026-06-15 | Endpoint 改為 `/bank/create_order`（原 `/coupon/create_order`），依呼叫端分類路徑 |
| 2026-06-12 | `user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: create_order

## 功能說明
讓發卡主機以 API Key 於信用卡授權後建立折抵訂單，神坊依 `order_id`、`member_id`、`brand_id`、`order_amount`、`card_last_four_digits` 與 `merchant_name` 執行 coupon 清算，扣點時依 `brand.treepoint_merchant_provider_key` 帶入點數帳務通路，並於同一個 DB transaction 內完成扣點、即時發券、既有券轉 `consumed`、建立訂單與事件後，僅回傳本次折抵金額。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - `member_id` 必須存在於神坊系統中
  - `order_id` 在神坊系統中必須唯一，重複傳入同一 `order_id` 將回傳錯誤
  - `brand_id` 必須存在於神坊系統中

## 使用情境
發卡主機於用戶刷卡授權成功後，同步呼叫此 API。神坊以 request 提供的 `brand_id` 作為唯一品牌來源，先取用既有 `available coupon`，再依 active campaign、剩餘點數與該 campaign 的 `max_redemptions_per_order` 決定是否即時發新券；執行扣點時，系統應依 `brand` 讀取其 `treepoint_merchant_provider_key`，作為點數帳務通路識別。

發卡主機需一併帶入該筆刷卡卡號後四碼及刷卡門市名稱（`merchant_name`），供神坊保存於訂單資料，後續由前台端查詢訂單時顯示。

若同一 `order_id` 已成功建立，任何再次收到的 `create_order` 請求皆不重做清算，直接回 `ORDER_ALREADY_EXIST`。若需查詢訂單完整資訊、用券明細與事件歷程，應另呼叫 `get_order`。

# Request
HTTP method: `POST`
Endpoint: `/bank/create_order`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{issuer_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| order_id | string | TRUE | FALSE | ❎ | 最多 64 字；僅限英數字與底線；全系統唯一 |
| member_id | string | TRUE | FALSE | ❎ | UUID |
| brand_id | string | TRUE | FALSE | ❎ | ULID |
| order_amount | integer | TRUE | FALSE | ❎ | > 0，單位為元 |
| card_last_four_digits | string | TRUE | FALSE | ❎ | 固定 4 字；僅接受 `0-9` |
| merchant_name | string | TRUE | FALSE | ❎ | 最多 64 字；刷卡當下的門市名稱（如「全家南京西路店」） |
| transaction_time | string | TRUE | FALSE | ❎ | 刷卡交易時間（UTC+8 ISO 8601）；呈現用途，不影響清算或券的時間計算 |

# Response
## Sample（JSON）

```json
{
  "discount_amount": 141
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| discount_amount | Integer | 本次實際折抵總金額（元） |

### 邏輯說明

- campaign 的 active 判斷：`rotation_campaigns` 中是否存在對應當前 active rotation 的記錄；active campaign 必須為 `type = auto`
- 即使該 brand 當前無 active campaign，只要用戶有 `available` 的舊券，仍應執行清算並使用舊券；無 active campaign 時僅跳過新券發行步驟，不視為錯誤

**既有券清算：**
1. 取出用戶在此 brand 下所有 `status = available` 且尚未過期的 coupons，依 `expired_at ASC`、`created_at ASC`、`coupon_id ASC` 排序（FIFO）
2. 逐張檢查：若單張券 `coupon_min_order_amount` 大於當下剩餘消費額，則跳過該券，繼續檢查下一張
3. 若該舊券 `campaign_id` 對應當前 active campaign，僅在本次已使用的 active-campaign 券數 `< max_redemptions_per_order` 時才可使用；一旦達上限，後續同 active campaign 舊券全部跳過
4. 若舊券屬於歷史 campaign，則不受 `max_redemptions_per_order` 限制，仍照 FIFO 與金額門檻規則使用
5. 所有被使用的既有券狀態改為 `consumed`

**新券發行與清算：**
1. 計算剩餘消費額：`order_amount - Σ（已使用既有券的 coupon_min_order_amount）`
2. 計算 per-order quota：`remaining_per_order_quota = max_redemptions_per_order - active_campaign_coupon_used_count`；若 `<= 0` 或無 active campaign，跳過新券發行
3. 計算 per-rotation quota：`remaining_per_rotation_quota = max_redemption_per_rotation - count(member_id, campaign_id, rotation_id 已發券數)`；若 `<= 0`，跳過新券發行
4. 本次可新發張數 = `min(剩餘消費額 // coupon_min_order_amount, point_balance // coupon_redeem_points, remaining_per_order_quota, remaining_per_rotation_quota)`
5. 執行扣點（依 `brand.treepoint_merchant_provider_key` 作帳務歸屬），並即時發對應張數新券，狀態為 `consumed`
6. 新券建立時，`expired_at = (issued_at 所在 UTC+8 日期 + coupon_valid_days) 的 23:59:59.999`

- `discount_amount` = Σ（本次所有 `consumed` coupon 的 `coupon_discount_amount`）
- 僅在同一個 DB transaction 內完成扣點、發新券、既有券轉 `consumed`、建立 order 與建立 order event 後，才視為建單成功
  > 是否以同一 DB transaction 進行待討論
- 建單成功後，訂單進入 `PROCESSING` 狀態，等待後續 `finalize_order`
- 若用戶在該 brand 下無任何 `available coupon`，且點數餘額也為 0（或無 active campaign 可發新券），則本次清算直接失敗並回 `NO_AVAILABLE_COUPON_AND_POINT`
- `card_last_four_digits`、`merchant_name`、`transaction_time` 均為顯示用途欄位，由發卡主機於建單時提供，神坊原樣保存於訂單資料（快照），供後續訂單查詢 API 回傳；不參與任何清算邏輯
- 券的 `issued_at` / `expired_at` 均以神坊**收到 request 的實際時間**為準，與 `transaction_time` 無關
- **rotation 邊界暫定：** 若 `transaction_time` 早於 `rotation.end_at`（交易發生在舊檔期內），但神坊收到 request 時當下時間已超過 `rotation.end_at`，**暫定仍以收到 request 時間為準**執行清算（不回溯舊 rotation）
- `max_redemption_per_rotation`：定義於 campaign 屬性；計數條件為同一 `member_id + campaign_id + rotation_id` 下曾發行（含 `consumed`、`settled`、`available`、`expired`）的 coupon 總數；涵蓋 auto 與 manual 兩種場景
- `create_order` response 僅回傳 `discount_amount`；若需訂單狀態、用券明細、事件歷程與卡號後四碼，應另呼叫 `get_order`
- 同一 `order_id` 只允許成功建立一次；任何再次收到的 `create_order` 請求皆回 `ORDER_ALREADY_EXIST`
- 重複 `create_order` 不得再次扣點、發券、改券狀態或新增事件

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `brand_id` 不存在：`BRAND_NOT_FOUND`
3. `order_id` 已存在：`ORDER_ALREADY_EXISTS`
4. 使用者未啟用該品牌自動兌換：`AUTO_REDEEM_NOT_ENABLED_FOR_BRAND`
5. 用戶無 `available coupon` 且點數為 0（或無 active campaign 可發新券）：`NO_AVAILABLE_COUPON_AND_POINT`
