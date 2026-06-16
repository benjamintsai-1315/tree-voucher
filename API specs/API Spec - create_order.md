---
title: API Spec - create_order
permalink: /api-specs/create-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-15 | Endpoint 改為 `/bank/create_order`（原 `/coupon/create_order`），依呼叫端分類路徑 |
| 2026-06-12 | `user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: create_order

## 功能說明
讓發卡主機以 API Key 於信用卡授權後建立折抵訂單，神坊依 `order_id`、`member_id`、`brand_id`、`cash_amount` 與 `card_last_four_digits` 執行 coupon 清算
扣點時依 `brand.treepoint_merchant_provider_key` 帶入點數帳務通路，並於同一個 DB transaction 內完成扣點、即時發券、既有券轉 `processing`、建立訂單與事件後，僅回傳本次折抵金額。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - `member_id` 必須存在於神坊系統中
  - `order_id` 在神坊系統中必須唯一，重複傳入同一 `order_id` 將回傳錯誤
  - `brand_id` 必須存在且目前具備 active campaign

## 使用情境
發卡主機於用戶刷卡授權成功後，同步呼叫此 API。神坊以 request 提供的 `brand_id` 作為唯一品牌來源，先取用既有 `available coupon`，再依 active campaign、剩餘點數與該 campaign 的 `max_redemptions_per_order` 決定是否即時發新券；執行扣點時，系統應依 `brand` 讀取其 `treepoint_merchant_provider_key`，作為點數帳務通路識別。

發卡主機需一併帶入該筆刷卡卡號後四碼，供神坊保存於訂單資料，後續由前台端查詢訂單時顯示。

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
| brand_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| cash_amount | integer | TRUE | FALSE | ❎ | > 0，單位為元 |
| card_last_four_digits | string | TRUE | FALSE | ❎ | 固定 4 字；僅接受 `0-9` |

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
- 本 API 為「用戶進入系統」的觸發點之一，執行清算前須先進行 **lazy cleanup**：若 `member_id` 在 `member_selected_brands` 中的記錄 `rotation_key` 與當前 active rotation 不符，系統自動清除舊選擇，並為每個被清除品牌寫入 `SYSTEM_CLEAR_BRANDS` 事件（`occurred_at` = 舊 rotation 的 `end_time`）；清除後若本 `brand_id` 不再在用戶已選清單中，則回傳 `AUTO_REDEEM_NOT_ENABLED_FOR_BRAND`
- campaign 的 active 判斷改為確認其 `rotation_id` 對應的 rotation 是否為當前 active rotation（不再以 `campaign.start_at`/`end_at` 判斷）；active campaign 必須為 `type = auto`
- `discount_amount` = Σ（本次所有 processing coupon 的 `coupon_discount_amount`）
- 既有券只掃描 `status = available` 且尚未過期的 coupons，排序規則為 `expired_at ASC`、`created_at ASC`、`coupon_id ASC`
- 掃描過程中，若單張券 `coupon_min_order_amount` 大於當下剩餘消費額，則跳過該券，繼續檢查下一張
- 若舊券 `campaign_id` 對應當前 active campaign，僅在本次已使用的 active-campaign 券數 `< active_campaign.max_redemptions_per_order` 時才可使用；一旦達上限，後續同 active campaign 舊券全部跳過
- 若舊券屬於歷史 campaign，則不受 `max_redemptions_per_order` 限制，仍照 FIFO 與金額門檻規則使用
- 本次依 active campaign 即時發新券前，先計算 `remaining_active_campaign_quota = active_campaign.max_redemptions_per_order - active_campaign_coupon_used_count
- 本次可新發張數 = `min(剩餘消費額 // coupon_min_order_amount, point_balance // coupon_redeem_points, remaining_active_campaign_quota)`
- 若 `remaining_active_campaign_quota <= 0`，本次不得再新發任何 active-campaign 券
- 僅在同一個 DB transaction 內完成扣點、發新券、既有券轉 `processing`、建立 order 與建立 order event 後，才視為建單成功
  > 是否以同一 DB transaction 進行待討論
- 建單成功後，訂單進入 `PROCESSING` 狀態，等待後續 `finalize_order`
- 若用戶在該 `brand` 下無任何 `available coupon`，且點數餘額也為 0，則本次清算直接失敗並回 `NO_AVAILABLE_COUPON_AND_POINT`
- 執行扣點時，系統應依 `brand.treepoint_merchant_provider_key` 進行點數帳務歸屬
- `card_last_four_digits` 為顯示用途欄位，由發卡主機於建單時提供，神坊原樣保存於訂單資料，供後續訂單查詢 API 回傳
- `create_order` response 僅回傳 `discount_amount`；若需訂單狀態、用券明細、事件歷程與卡號後四碼，應另呼叫 `get_order`
- 新券建立時，`expired_at = (issued_at 所在 UTC+8 日期 + coupon_valid_days) 的 23:59:59.999`
- 同一 `order_id` 只允許成功建立一次；任何再次收到的 `create_order` 請求皆回 `ORDER_ALREADY_EXIST`
- 重複 `create_order` 不得再次扣點、發券、改券狀態或新增事件

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. `brand_id` 不存在：`BRAND_NOT_FOUND`
3. `order_id` 已存在：`ORDER_ALREADY_EXISTS`
4. 使用者未啟用該品牌自動兌換：`AUTO_REDEEM_NOT_ENABLED_FOR_BRAND`
5. 用戶無 `available coupon` 且點數為 0：`NO_AVAILABLE_COUPON_AND_POINT`
6. 該品牌目前無 active campaign：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
