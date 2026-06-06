# API: create_order

## 功能說明
讓發卡主機以 API Key 於信用卡授權後建立折抵訂單，神坊依 `order_id`、`user_id`、`brand_id`、`cash_amount` 與 `card_last_four_digits` 執行 coupon 清算；扣點時依 `brand.treepoint_merchant_provider_key` 帶入點數帳務通路，並於同一個 DB transaction 內完成扣點、即時發券、既有券轉 `processing`、建立訂單與事件後，回傳本次折抵結果。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - API Key 須為發卡主機專屬授權，不接受前台端或其他呼叫方的 API Key
  - `order_id` 必須由發卡主機編制，且於神坊系統內具唯一性
  - `brand_id` 必須存在且目前具備 active campaign
  - `user_id` 必須存在，且該用戶已啟用該 `brand` 的自動兌換設定

## 使用情境
發卡主機於用戶刷卡授權成功後，同步呼叫此 API。神坊以 request 提供的 `brand_id` 作為唯一品牌來源，先取用既有 `available coupon`，再依 active campaign 與剩餘點數決定是否即時發新券；執行扣點時，系統應依 `brand` 讀取其 `treepoint_merchant_provider_key`，作為點數帳務通路識別。

發卡主機需一併帶入該筆刷卡卡號後四碼，供神坊保存於訂單資料，後續由前台端查詢訂單時顯示。

若同一 `order_id` 已成功建立，任何再次收到的 `create_order` 請求皆不重做清算，直接回 `ORDER_ALREADY_EXIST`。

# Request
HTTP method: `POST`
Endpoint: `/coupon/create_order`
Content-Type: `application/json`

## Request Header（表格）
| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{issuer_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| order_id | string | TRUE | FALSE | ❎ | 最多 64 字；同一系統內唯一 |
| user_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| brand_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| cash_amount | integer | TRUE | FALSE | ❎ | > 0，單位為元 |
| card_last_four_digits | string | TRUE | FALSE | ❎ | 固定 4 字；僅接受 `0-9` |

# Response
## Sample（JSON）

```json
{
  "order_id": "ORD_20251001_00001",
  "user_id": "USR_000123",
  "brand_id": "BRAND_FAMILYMART",
  "cash_amount": 620,
  "card_last_four_digits": "1234",
  "discount_amount": 141,
  "order_status": "PROCESSING",
  "finalized_at": null,
  "coupons_used": [
    {
      "coupon_id": "CPN_001",
      "campaign_id": "old_campaign",
      "unit_cash_amount": 400,
      "unit_point_amount": 100,
      "unit_discount_amount": 120,
      "expired_at": "2025-10-31T23:59:59.999+08:00",
      "type": "EXISTING"
    },
    {
      "coupon_id": "CPN_002",
      "campaign_id": "new_campaign",
      "unit_cash_amount": 100,
      "unit_point_amount": 20,
      "unit_discount_amount": 21,
      "expired_at": "2025-11-30T23:59:59.999+08:00",
      "type": "NEWLY_ISSUED"
    }
  ],
  "created_at": "2025-10-01T14:30:00+08:00"
}
```

## Response items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼，由發卡主機提供 |
| user_id | String | 神坊用戶識別碼 |
| brand_id | String | 對應 brand 識別碼 |
| cash_amount | Integer | 本次刷卡金額（元） |
| card_last_four_digits | String | 該筆刷卡卡號後四碼，固定 4 碼數字字串 |
| discount_amount | Integer | 本次實際折抵總金額（元） |
| order_status | String | 訂單當前狀態；成功建立後固定回 `PROCESSING` |
| finalized_at | String \| null | 訂單最終化時間；`PROCESSING` 時為 `null` |
| coupons_used | Array | 本次被使用的券明細，包含原券夾既有券與本次即時發新券 |
| created_at | String | 訂單建立時間（UTC+8 ISO 8601） |

### coupons_used
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| coupon_id | String | 券識別碼 |
| campaign_id | String | 該券所屬 campaign 識別碼 |
| unit_cash_amount | Integer | 該券對應的消費門檻金額（元） |
| unit_point_amount | Integer | 該券建立時所對應的點數成本 |
| unit_discount_amount | Integer | 該券折抵金額（元） |
| expired_at | String | 該券固定到期時間（UTC+8 ISO 8601，毫秒精度） |
| type | String | `EXISTING`：原券夾既有券；`NEWLY_ISSUED`：本次即時兌換產生 |

### 邏輯說明
- `discount_amount` = Σ `coupons_used[].unit_discount_amount`
- 既有券只掃描 `status = available` 且尚未過期的 coupons，排序規則為 `expired_at ASC`、`created_at ASC`、`coupon_id ASC`
- 掃描過程中，若單張券 `unit_cash_amount` 大於當下剩餘消費額，則跳過該券，繼續檢查下一張
- 僅在同一個 DB transaction 內完成扣點、發新券、既有券轉 `processing`、建立 order 與建立 order event 後，才視為建單成功
- 建單成功後，訂單進入 `PROCESSING` 狀態，等待後續 `finalize_order`
- 執行扣點時，系統應依 `brand.treepoint_merchant_provider_key` 進行點數帳務歸屬
- `card_last_four_digits` 為顯示用途欄位，由發卡主機於建單時提供，神坊原樣保存於訂單資料，供後續訂單查詢 API 回傳
- 新券建立時，`expired_at = (issued_at 所在 UTC+8 日期 + coupon_valid_days) 的 23:59:59.999`
- 同一 `order_id` 只允許成功建立一次；任何再次收到的 `create_order` 請求皆回 `ORDER_ALREADY_EXIST`
- 重複 `create_order` 不得再次扣點、發券、改券狀態或新增事件

## 400 錯誤回傳（TYPE: MESSAGE）
1. API Key 非發卡主機授權：`CALLER_NOT_AUTHORIZED`
2. `order_id` 已存在：`ORDER_ALREADY_EXIST`
3. `user_id` 不存在：`USER_NOT_FOUND`
4. `brand_id` 不存在：`BRAND_NOT_FOUND`
5. 該品牌目前無 active campaign：`BRAND_HAS_NO_ACTIVE_CAMPAIGN`
6. 使用者未啟用該品牌自動兌換：`AUTO_REDEEM_NOT_ENABLED_FOR_BRAND`
7. `card_last_four_digits` 格式不合法：`INVALID_CARD_LAST_FOUR_DIGITS`
