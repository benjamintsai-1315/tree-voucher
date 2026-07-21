---
title: API Spec - create_order
permalink: /api-specs/create-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-21 | 效能討論定案：`get_member_orders` 的 `coupon_usage_summary`／`point_used` 改為建單當下即計算並寫入 order 記錄的快照，取代原本查詢當下即時 JOIN／GROUP BY 聚合，降低列表查詢運算成本並避免大量用券訂單的 response 過大；新增「`get_member_orders` 用券摘要快照」段落 |
| 2026-07-21 | 訂單狀態生命週期表引用的 `batch_finalize_orders` action 值同步改為小寫 `complete`/`cancel`（原 `COMPLETED`/`CANCELLED`），與該 API spec 本次調整對齊 |
| 2026-07-16 | response 新增 `created_at`：order 於神坊資料庫中的建立時間（stage 1 建單當下），供發卡主機對帳參考 |
| 2026-07-16 | 簡化扣點逾時處理：同步階段與 cronjob 階段對「確認成功」的處理動作原本完全相同（皆為呼叫返點退點），故移除同步階段的查詢步驟，改為 timeout 後直接標記「點數結果未定」交每日 cronjob 統一查詢與退點，避免重複查詢 |
| 2026-07-14 | 修正前次誤植：點數系統其實仍可查詢「用點結果確認」（成功/失敗/timeout），只是確認成功時**目前無法同時取得** `tree_points`/`cub_points` 細部拆分，故此分支改為呼叫返點（`return_point`）退點，而非整段查詢機制都不可用；查詢＋每日 04:00 cronjob 對帳機制維持現行有效，僅「確認成功」分支的處理方式待未來支援拆分查詢後才改回續行發券 |
| 2026-07-14 | 修正扣點逾時處理與實際能力不符：點數系統目前無法查詢扣點結果與 tree/cub 細部拆分，故 timeout 時目前僅能一律呼叫退點、視新券段為失敗；原「用點結果確認＋每日 cronjob 對帳」設計移列為未來優化方向 |
| 2026-07-14 | response 欄位 `summary` 更名為 `coupon_summary`，語意不變 |
| 2026-07-13 | 修正前次誤植：`summary.existing.tree_points`/`cub_points` 不應強制為 `0`，應列出該分組舊券於其**原始發行時**所使用之點數（歷史組成，非本次消耗）；是否為本次新消耗已由 `new_issued`／`existing` 分組本身區分，無需另外歸零 |
| 2026-07-13 | 新券段新增品牌入選前置條件：`member_selected_brands` 須存在 `member_id + brand_id + rotation_id`（當前 active rotation）完全符合之記錄才進入新券清算；未入選僅跳過新券段，舊券照常清算；未入選且無可用舊券歸入 `NO_ACTIVE_CAMPAIGN` |
| 2026-07-13 | 補註 `pending` 滯留訂單（stage 2 中斷未完成）暫無自動收斂機制，處置方式由營運團隊另行討論 |
| 2026-07-13 | response 對帳結構簡化：移除逐張 `coupons_used[]` 明細與 `points_used`，改為 `summary`（`new_issued`／`existing` 兩組彙總，各含 `discount_amount`/`tree_points`/`cub_points`）；`existing` 因舊券點數已於原始發行時扣除，`tree_points`/`cub_points` 固定為 `0` |
| 2026-07-13 | `max_points_per_rotation`（rotation 屬性、跨品牌合計點數上限）更名為 `max_points_per_member`，語意不變 |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`（清算完成、待終結）、`failed` 更名為 `error`（清算完成、失敗）；原「`processing`＝清算中」之暫態定義移除，該過程期間狀態維持 `pending` 至清算結束 |
| 2026-07-09 | response 新增 `coupons_used[]` 對帳明細：每張券含 `is_new_issued`、`discount_amount`、`redeem_points` 及**本次**消耗之 `tree_points`/`cub_points`（`cub_points` 為銀行發行點數，供對帳）；舊券（`is_new_issued=false`）本次不扣點，`tree_points`/`cub_points` 皆為 0；同一份明細同步加入 `bank_get_order` 供事後重查 |
| 2026-07-08 | 前台 `get_order` 廢除，訂單查詢導引改為 `bank_get_order`（發卡主機端）；前台不提供單筆訂單明細 |
| 2026-07-08 | 定義 `order.status` 生命週期（`pending`→`processing`→`waiting_finalization`/`failed`→`completed`/`cancelled`），取代舊二態 `PROCESSING`/`FAILED`；明訂兩段 DB transaction（stage 1 建單+既有券段、stage 2 新券段 update 併回）；成敗回歸單一條件 `discount_amount > 0`；新券段失敗區分「點數端失敗（走 retry/cronjob）」與「我方失敗（孤兒點數、人工善後）」，兩者皆不改變判定 |
| 2026-07-07 | 收斂待定事項：discount=0 回碼優先序定案為 400 清單編號順序（4→5→6→7→8）；跨品牌 `max_points_per_rotation` race condition 移交 RD 技術規格；`failed` 訂單可查性定案（`get_member_orders` 剔除、admin status filter 可查、`bank_get_order` 全回） |
| 2026-07-07 | 新券段重排步驟並改為**依序發券**（不再先算 min 一次發行）；移除 per-order quota 檢查與 `MEMBER_EXCEED_PER_ORDER_QUOTA`（能進新券段即代表 per-order 未占滿）；`brand_id` 不再前置檢查、移除 `BRAND_NOT_FOUND`（不存在者自然落入 `NO_ACTIVE_CAMPAIGN`）；新增扣點逾時與 retry/每日 cronjob 對帳機制（銀行可接受 15 秒、`order_id` 與點數扣點交易一對一） |
| 2026-07-07 | `AUTO_REDEEM_NOT_ENABLED_FOR_BRAND` 更名為 `AUTO_REDEEM_NOT_ENABLED`，釐清為**會員層級**（`members.auto_redeem_enabled`）暫停，品牌無獨立 auto disable；補述扣點成功但產券寫入失敗屬 5xx 非預期錯誤（需人工介入），不列入 `error_type` |
| 2026-07-06 | 清算改為「既有券段（必成）／新券段（best effort）」兩段結構；成功條件改為 `discount_amount > 0`，否則建立 `FAILED` 訂單並記 `error_type`；重整 400 失敗碼（新增 `NO_ACTIVE_CAMPAIGN`、`ORDER_AMOUNT_BELOW_MIN_AMOUNT`、`MEMBER_EXCEED_PER_ORDER_QUOTA`、`MEMBER_EXCEED_PER_ROTATION_POINT_LIMIT`）；`max_redemption_per_rotation`(campaign 屬性、計張數) → `max_points_per_rotation`(rotation 屬性、跨品牌計點數)；quota 值 `0` 一律代表無上限；`ORDER_ALREADY_EXIST` 統一為 `ORDER_ALREADY_EXISTS`；`rotation_campaigns`→`brand_rotation_campaigns`、`rotation.end_at`→`end_time`、`finalize_order`→`batch_finalize_orders` |
| 2026-07-02 | response 新增 `points_used`（`tree_points` / `cub_points`）；新增點數分配邏輯（cub_points 優先）與 `treelife_use_point_log` 說明 |
| 2026-07-02 | 新增 `transaction_time` request 欄位（呈現用）；新增 `max_redemption_per_rotation` campaign 屬性與對應 quota 檢查；新增 rotation 邊界暫定說明 |
| 2026-07-01 | `brand_id` 限制改為 ULID |
| 2026-06-25 | 新增 `store_name` request 欄位（必填）；快照保存於 `orders` 表，供前台訂單列表顯示門市名稱 |
| 2026-06-25 | 放寬邊界檢查：`brand_id` 不再要求必須具備 active campaign；無 active campaign 時仍可使用既有 `available` 舊券；移除 `BRAND_HAS_NO_ACTIVE_CAMPAIGN` 錯誤碼 |
| 2026-06-25 | `cash_amount` 改名為 `order_amount`；移除 lazy cleanup 說明（見 PRD）；邏輯說明改為既有券清算 / 新券發行兩段結構 |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled` |
| 2026-06-15 | Endpoint 改為 `/bank/create_order`（原 `/coupon/create_order`），依呼叫端分類路徑 |
| 2026-06-12 | `user_selected_brands` → `member_selected_brands`；`USER_NOT_FOUND` → `MEMBER_NOT_FOUND` |

# API: create_order

## 功能說明
讓發卡主機以 API Key 於信用卡授權後建立折抵訂單。神坊依 `order_id`、`member_id`、`brand_id`、`order_amount`、`card_last_four_digits` 與 `store_name` 執行 coupon 清算，扣點時依 `brand.treepoint_merchant_provider_key` 帶入點數帳務通路。

清算分兩段：**既有券段**（使用既有 `available` 舊券、轉 `consumed`、建立訂單與事件）與**新券段**（扣點、即時發新券）。唯有本次實際折抵金額 `discount_amount > 0` 才算建單成功（訂單進入 `processing`）並回傳折抵金額；折抵金額為 0 則訂單標記 `error` 並回對應失敗碼。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - `member_id` 必須存在於神坊系統中
  - `order_id` 在神坊系統中必須唯一，重複傳入同一 `order_id`（含先前已建立的 `failed` 訂單）將回傳錯誤；`order_id` 與點數系統扣點交易為一對一關係
  - `brand_id` 不另做前置存在性檢查（不存在/無效者於清算階段自然導致 discount=0）
  - 來源 IP 需在白名單內
    > note: API key & IP WhiteList 皆存在 parameter store 內 


## 使用情境
發卡主機於用戶刷卡授權成功後，同步呼叫此 API。神坊以 request 提供的 `brand_id` 作為唯一品牌來源，先取用既有 `available coupon`，再依 active campaign、會員自動兌換設定、品牌入選狀態（`member_selected_brands`）、剩餘點數與各項 quota 決定是否即時發新券；執行扣點時，系統應依 `brand` 讀取其 `treepoint_merchant_provider_key`，作為點數帳務通路識別。

發卡主機需一併帶入該筆刷卡卡號後四碼及刷卡門市名稱（`store_name`），供神坊保存於訂單資料，後續由前台端查詢訂單時顯示。

若同一 `order_id` 已建立（無論 `waiting_finalization` 或 `failed`），任何再次收到的 `create_order` 請求皆不重做清算，直接回 `ORDER_ALREADY_EXISTS`。發卡主機若需查詢訂單狀態與折抵金額，應另呼叫 `bank_get_order`。

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
| store_name | string | TRUE | FALSE | ❎ | 最多 64 字；刷卡當下的門市名稱（如「全家南京西路店」） |
| transaction_time | string | TRUE | FALSE | ❎ | 刷卡交易時間（UTC+8 ISO 8601）；呈現用途，不影響清算或券的時間計算 |

# Response
## Sample（JSON）

```json
{
  "discount_amount": 109,
  "created_at": "2026-07-16T14:30:05.123+08:00",
  "coupon_summary": {
    "new_issued": { "discount_amount": 46, "tree_points": 30, "cub_points": 10 },
    "existing": { "discount_amount": 63, "tree_points": 25, "cub_points": 38 }
  }
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| discount_amount | Integer | 本次實際折抵總金額（元），成功建單時必 `> 0`；等於 `coupon_summary.new_issued.discount_amount + coupon_summary.existing.discount_amount` |
| created_at | String | 該筆 order 於神坊資料庫中建立的時間（UTC+8 ISO 8601，毫秒精度），即 stage 1 建立 order 當下的時間；供發卡主機對帳參考，與 request 帶入的 `transaction_time`（刷卡時間）無關 |
| coupon_summary | Object | 本次折抵金額與點數消耗，依新發券／既有券分組彙總，見下表 |

### coupon_summary

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| new_issued | Object | 本次訂單**新券段**即時發行之新券的彙總，見下表 |
| existing | Object | 本次訂單**既有券段**使用之舊券的彙總，見下表 |

`new_issued` 與 `existing` 皆為同一結構：

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| discount_amount | Integer | 該分組本次折抵金額合計（元） |
| tree_points | Integer | `new_issued`：本次訂單消耗的小樹點(生活)總數；`existing`：該分組舊券於其**原始發行時**所使用的小樹點(生活)總數（非本次消耗，僅呈現歷史組成，是否為本次消耗以所屬分組區分） |
| cub_points | Integer | `new_issued`：本次訂單消耗的小樹點(信用卡)總數；`existing`：該分組舊券於其**原始發行時**所使用的小樹點(信用卡)總數（原因同上） |

### 邏輯說明

- campaign 的 active 判斷：`brand_rotation_campaigns` 中是否存在對應當前 active rotation 的記錄；active campaign 必須為 `type = auto`
- 即使該 brand 當前無 active campaign，只要用戶有 `available` 的舊券，仍應執行既有券段清算並使用舊券；無 active campaign 時僅跳過新券發行步驟，不視為錯誤
- 同理，若該**會員**已暫停自動兌換服務（`members.auto_redeem_enabled = false`，會員層級單一開關，非品牌層級），僅跳過新券發行步驟，既有 `available` 舊券仍照常清算
- 同理，若該品牌**未入選**（`member_selected_brands` 中不存在 `member_id + brand_id + rotation_id`〔當前 active rotation〕完全符合之記錄，含 lazy cleanup 清空後的狀態），僅跳過新券發行步驟，既有 `available` 舊券仍照常清算

**既有券段（清算成功即 commit）：**
1. 取出用戶在此 brand 下所有 `status = available` 且尚未過期的 coupons，依 `expired_at ASC`、`created_at ASC`、`coupon_id ASC` 排序（FIFO）
2. 逐張檢查：若單張券 `coupon_min_order_amount` 大於當下剩餘消費額，則跳過該券，繼續檢查下一張
   - `coupon_min_order_amount`：門檻值，用來決定「共能使用幾張券」（累減剩餘消費額）
   - `coupon_discount_amount`：該券實際折抵金額，計入 `discount_amount`；兩者為不同概念，不相等屬正常設計
3. 若該舊券 `campaign_id` 對應當前 active campaign，僅在本次已使用的 active-campaign 券數 `< max_redemptions_per_order`（`max_redemptions_per_order = 0` 代表無上限）時才可使用；一旦達上限，後續同 active campaign 舊券全部跳過
4. 若舊券屬於歷史 campaign，則不受 `max_redemptions_per_order` 限制，仍照 FIFO 與金額門檻規則使用
5. 所有被使用的既有券狀態改為 `consumed`

**新券段（best effort，失敗不推翻既有券段）：**
1. 計算剩餘消費額：`order_amount - Σ（已使用既有券的 coupon_min_order_amount）`
2. 若無 active campaign、該會員 `members.auto_redeem_enabled = false`（會員層級暫停自動兌換）、或該品牌未入選（`member_selected_brands` 無 `member_id + brand_id + rotation_id` 完全符合之記錄），跳過新券發行
3. 計算 per-rotation 點數 quota：`max_points_per_member = 0` 時視為無上限；否則
   `remaining_rotation_point_budget = max_points_per_member - used_rotation_points`
   其中 `used_rotation_points = Σ（該 member 於當前 rotation 內已發行 coupon 的 coupon_redeem_points）`（跨品牌、跨 campaign 合計，含 `consumed`/`settled`/`available`/`expired` 全狀態）；若 `remaining_rotation_point_budget <= 0` 跳過新券發行
   - 註：新券段**不檢查** per-order 張數上限（`max_redemptions_per_order`）。該上限僅在既有券段對 active-campaign 舊券計數；能進入新券段即代表 per-order 尚未占滿，不存在「因 per-order 上限而無法發任何新券」的情境
4. 取會員點數餘額 `point_balance`
5. **依序發券**（不需先算 min 再一次發行）：自第一張起，逐張檢查以下條件是否**同時成立**——(a) 剩餘消費額 ≥ `coupon_min_order_amount`；(b) 剩餘點數 ≥ `coupon_redeem_points`；(c) `remaining_rotation_point_budget ≥ coupon_redeem_points`（無上限則略過 c）。成立則計入一張並自剩餘消費額、剩餘點數、`remaining_rotation_point_budget` 各扣減對應值，重複至任一條件不成立為止
6. 執行扣點：依上一步決定的張數與總點數，呼叫 treelife-api 扣點（依 `brand.treepoint_merchant_provider_key` 作帳務歸屬）
7. 扣點成功後即時建立對應張數新券，狀態為 `consumed`；`expired_at = (issued_at 所在 UTC+8 日期 + coupon_valid_days) 的 23:59:59.999`；`coupon_valid_days = 0` 代表當日到期（即 issued_at 當日 `23:59:59.999`）
   - **我方失敗**：若扣點已成功但此步發券寫入失敗，該批新券不計入折抵（產生孤兒點數），依「建單成敗判定」僅以舊券折抵決定訂單狀態，善後見下方兩種失敗類型表
8. **扣點失敗或逾時（treelife-api error / timeout，屬點數端失敗）**：依下方「扣點逾時處理」處理。最終無法完成扣點時跳過整個新券段（不發新券）；若既有券段已產生折抵（`discount_amount > 0`）→ `processing`；若既有券段亦無折抵→ `error`（`TREELIFE_ERROR`）

**扣點逾時處理：**
- 發卡主機可接受 `create_order` 於 **15 秒內**回覆；樹配券與點數系統的 `order_id` 為**一對一關係**（同一 `order_id` 對應點數系統的扣點交易，供結果確認與退還使用）
- **同步階段（15 秒內）**：呼叫 treelife-api 扣點後若 timeout，不在同步階段查詢確認，直接標記該 order 為「點數結果未定，待 cronjob 處理」；既有券段有折抵則視為成功（`processing`）、否則回 `TREELIFE_ERROR`
- **每日 04:00 cronjob 對帳**：對標記「點數結果未定」的 order，呼叫「用點結果確認」查詢扣點結果：
  - 確認**成功** → 因點數系統目前無法同時回傳 `tree_points`/`cub_points` 細部拆分，缺此資料無法正確發券記帳，且先前已回覆發卡主機為失敗、未發券，故呼叫**返點**退點（`return_point.note = "國泰優惠兌換_樹配卷_票券產生失敗"`）
  - 確認**失敗** → 不處理（點數未被扣，狀態一致）
  - 仍 **timeout** → 標記為「有問題」，透過告警通知團隊人工介入

**未來優化方向（原設計，待點數系統支援結果查詢後啟用）：**
- 待點數系統的「用點結果確認」可同步回傳 `tree_points`/`cub_points` 細部拆分後，可改為同步階段 timeout 後立即查詢確認：確認**成功**時視同扣點成功，續行發券，並將 `tree_points`/`cub_points` 等資料回寫樹配券平台（不再需要退點、也不需等待 cronjob）

**折抵與扣點：**
- `discount_amount` = Σ（本次所有 `consumed` coupon 的 `coupon_discount_amount`）（含既有券段與新券段）
- 扣點時呼叫 treelife-api，treelife-api 回傳本批次實際使用的 `tree_points`（小樹點生活）與 `cub_points`（小樹點信用卡）**總數**；由神坊定義各券分配多少 cub/tree
- 點數按券分配並寫入 `treelife_use_point_log`：cub_points 優先分配給先發行的券；分配規則為每張券消耗 `coupon_redeem_points` 點，先由 cub_points 填滿，不足時才使用 tree_points；`used_tree_points + used_cub_points` = 該券的 `coupon_redeem_points`，且各券加總須等於 treelife-api 回傳之總數
- `coupon_summary.new_issued.tree_points` / `coupon_summary.new_issued.cub_points` 為 treelife-api 回傳的全批次總數，直接轉入 response；`coupon_summary.existing.tree_points`/`cub_points` 則取自該分組每張舊券於其原始發行訂單寫入 `treelife_use_point_log` 的 `used_tree_points`/`used_cub_points` 加總（歷史值，非本次消耗）

**`coupon_summary` 對帳彙總（供發卡主機）：**
- `coupon_summary` 依新券段／既有券段分組彙總，非逐張券明細；`new_issued` 對應本次即時發行的新券，`existing` 對應本次使用的既有舊券
- `existing` 分組列出的點數為該些舊券**原始發行時**的歷史點數組成，並非本次訂單新消耗；該分組是否為本次新消耗，由 `new_issued`／`existing` 兩個分組本身即可判斷，不需另外歸零
- 對帳恆等式：`coupon_summary.new_issued.discount_amount + coupon_summary.existing.discount_amount == discount_amount`
- `cub_points`（小樹點信用卡）為銀行發行點數，是發卡主機對帳的主要依據；`tree_points`（小樹點生活）為神坊端點數，一併列出供完整核對

**`get_member_orders` 用券摘要快照（效能考量）：**
- 建單完成時（既有券段與新券段皆處理完畢後），同步將依 `campaign_name` + `is_new_issued` 分組聚合的用券摘要（含 `discount_amount`、`quantity`）與 `point_used` 寫入該筆 order 記錄（例如 `orders.coupon_usage_summary` JSON 欄位），供 `get_member_orders` 直接讀取快照回傳，不需在列表查詢當下即時 JOIN／GROUP BY 聚合——降低列表查詢的即時運算成本，同時避免單筆訂單使用大量券（例如 20 張）時 response 資料量過大
- 此快照與本 API 回應的 `coupon_summary`（`new_issued`／`existing` 兩組彙總，供發卡主機對帳）粒度不同：`coupon_usage_summary` 快照另依 `campaign_name` 進一步分組，供前台會員訂單列表顯示用途
- 快照於建單當下寫入後即固定，不隨後續 coupon 狀態變化（如 `consumed → settled`）而更動，僅反映建單當下的用券結果

**訂單狀態（`order.status`）生命週期：**

| 狀態 | 意義 | 進入時機 |
| ---- | ---- | ---- |
| `pending` | 剛建立，涵蓋清算執行中（既有券段 + 新券段），無獨立的「清算中」狀態值 | stage 1 一開始即建立 order（不論有無舊券） |
| `processing` | 清算完成、待終結 | 清算完成且 `discount_amount > 0`，等待 `batch_finalize_orders` |
| `error` | 清算完成、失敗 | 清算完成且 `discount_amount = 0` |
| `completed` | 已終結 | `batch_finalize_orders` action=`complete` |
| `cancelled` | 已終結（取消） | `batch_finalize_orders` action=`cancel` |

> ⚠️ `pending` 滯留：若 stage 2 執行中系統中斷，訂單將停留於 `pending`（不出現於 `get_member_orders`、亦不可終結）。目前**無自動收斂機制**，滯留訂單之處置方式由營運團隊另行討論後補充。

**兩段 DB transaction 邊界：**
- **stage 1（既有券段）**：於單一 transaction 內建立 order（狀態維持 `pending`）、既有券段清算（舊券轉 `consumed`）、建立 order event 後 commit
- **stage 2（新券段）**：另一 transaction 執行扣點、發新券；完成後將新券的折抵與點數 **update 併回同一筆 order**
- 兩段皆於 15 秒同步窗內跑完才回覆發卡主機；response 的 `discount_amount` 為兩段合計

**成敗判定（單一條件，不受新券段失敗種類影響）：**
- 清算完成後 `discount_amount = Σ（既有券折抵 + 成功發出新券折抵）`
- **`discount_amount > 0` → `processing`**（成功），等待後續 `batch_finalize_orders`
- **`discount_amount = 0` → `error`**，記錄對應 `error_type`（見下方 400 清單 4～8），API 回傳該失敗碼

**新券段失敗的兩種類型（皆不改變上述判定，只影響善後）：**

| 失敗種類 | 情境 | 點數狀態 | 對訂單影響 | 後續處理 |
| ---- | ---- | ---- | ---- | ---- |
| **點數端失敗** | treelife-api 扣點 fail / timeout | 未扣、已扣但退還、或未定 | 跳過新券段，只計舊券折抵：有舊券折抵→`processing`；無→`error`（`TREELIFE_ERROR`） | 確認成功即退點；未定者交每日 04:00 cronjob 對帳（見上「扣點逾時處理」） |
| **我方失敗** | 扣點已成功、但神坊端發券寫入失敗 | 已扣（孤兒點數） | **不影響判定**，僅計舊券折抵：有舊券折抵→`processing`；無→`error` | 屬 5xx 非預期錯誤，人工事後補券或退還已扣點數 |

- **可查性**：`get_member_orders` 剔除 `error`；admin 端可經 status filter 查得；`bank_get_order` 不分 status 一律全回
- **冪等**：同一 `order_id` 只允許建立一次（不論最終為 `processing` 或 `error`，皆佔用 `order_id`）；任何再次收到的請求皆回 `ORDER_ALREADY_EXISTS`，不得再次扣點、發券、改券狀態或新增事件

**時間與 rotation 邊界：**
- `card_last_four_digits`、`store_name`、`transaction_time` 均為顯示用途欄位，由發卡主機於建單時提供，神坊原樣保存於訂單資料（快照），供後續訂單查詢 API 回傳；不參與任何清算邏輯
- 券的 `issued_at` / `expired_at` 均以神坊**收到 request 的實際時間**為準，與 `transaction_time` 無關；`expired_at` 的日界（`23:59:59.999` UTC+8、含邊界）與 rotation active 判定採相同精度與邊界規則
- **rotation 邊界暫定：** 若 `transaction_time` 早於 `rotation.end_time`（交易發生在舊檔期內），但神坊收到 request 時當下時間已超過 `rotation.end_time`，**暫定仍以收到 request 時間為準**執行清算（不回溯舊 rotation）
- `max_points_per_member`：定義於 **rotation 屬性**（非 campaign）；語意為「同一用戶於此 rotation 內、跨所有品牌與 campaign 合計可用的點數上限」；計數條件為同一 `member_id + rotation_id` 下已發行 coupon 的 `coupon_redeem_points` 加總；`0` 代表無上限
- `create_order` response 回傳 `discount_amount` 與 `coupon_summary`（新券段／既有券段彙總）；發卡主機若需事後重查訂單狀態與折抵金額，應另呼叫 `bank_get_order`（前台端不提供單筆訂單明細查詢）

## 400 錯誤回傳（TYPE: MESSAGE）

**前置驗證失敗（不建立訂單；優先序：member 相關最前）：**
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
3. `order_id` 已存在（含先前 `error` 訂單）：`ORDER_ALREADY_EXISTS`

> `brand_id` 不另做前置存在性檢查；不存在或無效的 `brand_id` 會自然落入清算流程（無此品牌舊券、無 active campaign）而導致 discount=0，歸入下方 `NO_ACTIVE_CAMPAIGN`。

**清算後折抵金額為 0（訂單標記 `error` 並記 `error_type`；`get_member_orders` 不回傳）：**
4. 無 active campaign 可發新券（含 `brand_id` 不存在/無效、該品牌未入選 `member_selected_brands`），且無符合門檻的可用舊券：`NO_ACTIVE_CAMPAIGN`
5. 該會員已暫停自動兌換服務（`members.auto_redeem_enabled = false`）而無法發新券，且無可用舊券：`AUTO_REDEEM_NOT_ENABLED`
6. 有 active campaign 但點數不足發任何新券，且無可用舊券：`NO_AVAILABLE_COUPON_AND_POINT`
7. 訂單金額未達可用券的最低消費門檻（含 `order_amount` 過小），本次無折抵：`ORDER_AMOUNT_BELOW_MIN_AMOUNT`
8. 已達該 rotation 的 per-rotation 點數上限而無法發新券，且無可用舊券：`MEMBER_EXCEED_PER_ROTATION_POINT_LIMIT`

**外部系統失敗：**
9. 扣點失敗/逾時且既有券段亦無折抵：`TREELIFE_ERROR`（若既有券段已有折抵則不回此碼，視為成功）

> DB transaction 失敗、或扣點成功但產券寫入失敗，均屬非預期錯誤，回 5xx 並需人工介入調查，不列入上述 MESSAGE 清單與 `error_type`。

---

## v1 待定事項（供 SA 討論）

1. **兩段之交易邊界**：既有券段（consumed + 建單 + event）commit 後，新券段（扣點 + 發新券）如何維持一致性——新券段成功時其 `consumed` 券與點數如何併入既有訂單（同筆 order 追加 vs 二階段提交），扣點成功但發券寫入失敗的補償策略。

> 已定案（非待定）：
> - **B 類（4～8）回碼優先序**：單筆清算同時符合多個 discount=0 原因時，依 400 清單編號順序判定（4 → 5 → 6 → 7 → 8）。
> - **跨品牌並發**：`max_points_per_member` 跨品牌共用點數池的 race condition 防超用機制，由 RD 於後續技術規格定義，不在本 spec 範圍。
> - **`error` 訂單可查性**：見上「訂單狀態生命週期」段之可查性定義。
