# Changelog

<!-- changelog subagent 會在此處插入最新條目 -->

## 2026-07-14 — get_coupons 補上 updated_at 欄位

- `SETTLED` bucket 的排序規則早已定義為依 `updated_at DESC`（finalize 時間），但 response schema 未實際回傳此欄位，說明與資料脫鉤
- 補上 `updated_at`（UTC+8 ISO 8601，毫秒精度）於 `coupons[]`，並將 sample 第二筆改為 `SETTLED` 狀態以對應說明

## 2026-07-14 — 收斂 last_brand_selection_changed_at 與 lazy cleanup 矛盾（AUD-036）

- 既有矛盾：`get_member_settings.md` 明訂「lazy cleanup 不影響 `last_brand_selection_changed_at`」，但 PRD Flow 4 與 Flow 5-1 兩處寫「lazy cleanup 換檔清空時需更新此欄位為舊 rotation 的 `end_time`」——此矛盾先前已被 `docs/reviews/2026-07-06-spec-audit.md`（AUD-036）標記為待釐清
- 決議定案：**lazy cleanup 不更新 `last_brand_selection_changed_at`**，此欄位僅於首次選牌、更換品牌時更新；PRD 兩處已同步修正，`get_member_settings.md` 維持原樣（本就正確）

## 2026-07-14 — get_member_orders coupon_usage_summary 新增新舊券區分

- 新增 `is_new_issued`（Boolean）：`true` 為本次訂單即時發行的新券、`false` 為本次使用的既有舊券，供前端做差異顯示
- 分組鍵同步調整為 `campaign_name` + `is_new_issued`：同一 campaign 若同時有新券與舊券被使用，分兩組回傳，不合併

## 2026-07-14 — 盤點修正：coupon id 未標示 ULID 之處

- `get_coupons.md`、`get_coupon_detail.md`：`id`（券識別碼）欄位說明補上 ULID 型別註記；sample 中 `CPN_001`/`CPN_002` 佔位字串改為 ULID 格式，避免誤導實際格式
- 已核對 `bank_get_order.md`（已正確標註 ULID）；已廢棄的 `get_order.md` 維持不動（歷史紀錄，不再是現行端點）
- `create_order.md`、`get_member_orders.md` 目前 response 皆不含 coupon 層級 `id` 欄位，不受影響

## 2026-07-14 — 修正兩個邏輯錯誤：get_coupon_wallet 範圍、get_coupon_detail 點數拆分

### get_coupon_wallet
- 範圍錯誤修正：品牌清單改為回傳過去一年內（查詢當下 T-366 天，含）有 coupon 發行紀錄的所有品牌，不再限於「當前 rotation 曾選過」的品牌
- 原範圍與 PRD 的 Coupon Wallet 定義（對 `coupons` 表的查詢投影，不綁定 rotation）互相矛盾，且會導致換檔後仍有可用舊券（FIFO 跨 rotation 可用）的品牌從券夾消失
- `brands: []` 條件同步改為「過去一年內無任何品牌換券紀錄」

### get_coupon_detail
- 新增 `tree_points`/`cub_points` 兩種點數明細（取自 `treelife_use_point_log`），`redeem_points` 保留為合計；原本只回傳合計數，不足以呈現「這張券當初動用了哪兩種點數各多少」

## 2026-07-13 — 修正 create_order summary.existing 點數欄位誤植

- 前次（本日稍早）將 `summary.existing.tree_points`/`cub_points` 定義為固定 `0`，理由是「舊券點數已於原始發行時扣除，非本次消耗」——這個理由沒錯，但不代表該顯示 `0`：`existing` 分組本身就已表明這不是本次新消耗，欄位應如實列出該些舊券**原始發行時**的歷史點數組成（取自 `treelife_use_point_log` 的 `used_tree_points`/`used_cub_points` 加總），而非強制歸零
- 已同步修正 `create_order.md`（Response items、對帳彙總說明、sample）與 PRD §5.2/§5.4 對應範例

## 2026-07-13 — PRD 復盤決議定案（品牌入選前置、CANCELLED 歸零、查詢期限、member_event_logs enum）

### create_order（決議 1、5）
- 新券段新增品牌入選前置條件：`member_selected_brands` 須存在 `member_id + brand_id + rotation_id`（當前 active rotation）完全符合之記錄才進入新券清算；未入選僅跳過新券段（舊券照常清算）；未入選且無可用舊券歸入既有錯誤碼 `NO_ACTIVE_CAMPAIGN`（不新增錯誤碼）
- 補註 `pending` 滯留訂單（stage 2 中斷）暫無自動收斂機制，處置方式由營運團隊另行討論

### batch_finalize_orders（決議 2）
- 明訂 `action = CANCELLED` 時訂單 `discount_amount` 歸零（與券狀態轉換同一 transaction），前台以 `discount_amount = 0` + `order_status = cancelled` 顯示「已退回券匣」

### get_member_settings_change_logs（決議 8）
- 「過去 1 年內」精確定義為查詢當下 **T-366 天**（含）；資料不清除，僅查詢範圍有上限

### member_event_logs（決議 6）
- `type` enum 定案為僅此 6 項：`activate_member`、`deactivate_member`、`change_selected_brands`、`system_clear_brands`、`disable_auto_redeem`、`enable_auto_redeem`（權威清單記於 CLAUDE.md）

### 舊表名清理（決議 3 盤點）
- `background.md`、`index.md`、`docs/README.md` 之 `member_brand_change_logs` / 舊 API 名殘留已更新
- `database-schema.md` 過時範圍遠超此表（`auth_status`、`rotation_campaigns`、訂單狀態舊 enum 等），經決議**廢棄並刪除**，schema 文件改由 RD 另行整理；README/docs 索引之對應連結同步移除

### 未排程（決議 7、9）
- 會員啟用歷史後台查詢 API 命名、`manual` campaign 兌換流程：留待未來規劃

## 2026-07-13 — PRD 全文同步至現行 spec（移入 docs/ 後之內容更新）

- §5/§6 全面改寫：兩段清算（既有券段必成／新券段 best effort）、依序發券、兩段 DB transaction、扣點 retry 與每日 cronjob 對帳、order.status 五態（`pending`/`processing`/`error`/`completed`/`cancelled`）
- 廢棄命名全數更新：`max_redemption_per_rotation` → `max_points_per_member`（rotation 屬性）、`finalize_order` → `batch_finalize_orders`（200 OK／`BATCH_REQUEST_ALREADY_EXISTS`）、`ORDER_ALREADY_EXIST` → `ORDER_ALREADY_EXISTS`、`cash_amount` → `order_amount`、`merchant_name` → `store_name`、`member_activation_logs`/`member_brand_change_logs` → `member_event_logs`
- create_order response 同步為 `discount_amount + summary`；Flow 6 券夾改為三層瀏覽並對齊 get_coupons 精簡欄位；Flow 1/§4.4/§9 補 `max_points_per_member`
- PRD §5.1 保留一則待決議標註：`member_selected_brands` 對 create_order 清算的作用未定義（原「用戶已選該品牌」觸發條件與現行 spec 不一致）

## 2026-07-13 — create_order response 對帳結構簡化：coupons_used[] → summary

- 移除逐張 `coupons_used[]` 明細與 `points_used`，改為 `summary`：`new_issued`／`existing` 兩組彙總，各含 `discount_amount`/`tree_points`/`cub_points`
- `existing`（既有券段）點數固定為 `0`：舊券的點數已於其原始發行訂單扣除，非本次消耗
- 對帳恆等式簡化為：`summary.new_issued.discount_amount + summary.existing.discount_amount == discount_amount`
- `bank_get_order` 目前仍保留原逐張 `coupons_used[]`/`points_used` 結構，尚未同步簡化，待確認是否比照調整

## 2026-07-13 — max_points_per_rotation 更名為 max_points_per_member ＋ get_current_rotation 補跟 quota 規則變更

### 命名校正（影響 CLAUDE.md／create_order.md／get_current_rotation.md）
- `max_points_per_rotation`（rotation 屬性、跨品牌合計點數上限）更名為 `max_points_per_member`，語意不變
- `get_current_rotation` 此前未跟上 2026-07-06/07-08 已定案的 quota 規則變更：campaigns 陣列移除已廢棄的 `max_redemption_per_rotation`（campaign 屬性、計張數），新增 rotation 層級的 `max_points_per_member` 欄位

## 2026-07-13 — order.status 實際欄位值校正（六態→五態）＋ get_member_orders 補齊列表畫面欄位

### order.status 命名校正（影響 create_order／bank_get_order／batch_finalize_orders／get_member_orders／CLAUDE.md）
- 實際 DB 欄位值為五態，非先前文件所載六態：`waiting_finalization` 更名為 `processing`；`failed` 更名為 `error`
- 原「`processing`＝清算中」之暫態定義自 enum 移除，該過程期間狀態維持 `pending` 直到清算結束（不落地為獨立的清算中狀態）
- `get_member_orders` 可見狀態相應改為 `processing` \| `completed` \| `cancelled`（剔除 `pending`、`error`）

### get_member_orders 新增前端列表畫面欄位
- 新增 `store_name`：`create_order` 自 2026-06-25 起已有此快照欄位（供前台訂單列表顯示門市名稱），此前漏未於 `get_member_orders` 回傳，此次補齊，原樣呈現不做品牌/門市對應轉換
- 新增 `coupon_usage_summary[]`：依 `campaign_name` 分組聚合的券使用摘要（`campaign_name`、`discount_amount`、`quantity`），非逐張 `coupons_used` 明細，不影響「前台不提供單筆訂單明細查詢」的既有原則
- 新增 `point_used`：本次訂單**新發券**部分消耗的 `tree_points`/`cub_points`；沿用既有券不產生新的點數消耗，故不重複列出
- 訂單取消（`order_status = cancelled`）時的顯示邏輯純依既有欄位判斷：`discount_amount = 0` 且 `order_status = cancelled`，前端據此顯示「已退回券匣」，不新增額外旗標欄位；`coupon_usage_summary[].discount_amount` 於取消訂單仍為原始計算值，僅前端顯示邏輯依 `order_status` 切換

## 2026-07-13 — 前台券 API 依前端頁面需求校準（get_coupons 精簡化、get_coupon_detail 有效期間定義）

### get_coupon_detail
- 明確定義 `created_at` 即為券「有效期間」之起始時間，與 `expired_at`（迄）合組完整起訖區間
- `created_at` 補齊毫秒精度，與 `expired_at` 一致

### get_coupons
- Response 精簡化：`coupons[]` 移除列表畫面不需要的 `brand`、`redeem_points`、`discount_rate`、`max_redemptions_per_order`、`created_at`；`campaign` 巢狀物件改為扁平 `campaign_name`
- 同一狀態 bucket 排序規則調整：`AVAILABLE`/`CONSUMED`/`EXPIRED` 改為 `expired_at DESC`、`id ASC`；`SETTLED` 改依 `updated_at DESC`（finalize 時間）、`id ASC`（原統一規則為 `expired_at ASC`、`created_at ASC`、`id ASC`）

## 2026-07-09 — create_order / bank_get_order 新增 coupons_used[] 對帳明細

### 發卡主機對帳明細
- `create_order` 與 `bank_get_order` response 新增 `coupons_used[]` 陣列，列出本次訂單所用的所有券（含舊券與新券），兩支 API 同結構
- 每張券含 `is_new_issued`（是否本次訂單即時發行）、`discount_amount`、`redeem_points`，以及**本次**消耗之 `tree_points`/`cub_points` 點數拆分
- 舊券（`is_new_issued = false`）本次不扣點，`tree_points`/`cub_points` 固定為 `0`（歷史成本記於 `redeem_points`）
- `cub_points`（小樹點信用卡）為銀行發行點數，是發卡主機對帳的主要依據；`tree_points`（小樹點生活）為神坊端點數，一併列出供完整核對
- 對帳恆等式：`Σ coupons_used[].tree_points == points_used.tree_points`、`Σ coupons_used[].cub_points == points_used.cub_points`、`Σ coupons_used[].discount_amount == discount_amount`
- `bank_get_order` 提供事後批次對帳重查（明細與 `create_order` 建單當下回傳者一致）；`failed` 訂單 `coupons_used[]` 為空陣列、`points_used` 皆為 0

## 2026-07-08 — create_order 兩段清算與 order 狀態機定案（SA reviewed）

### Order 狀態機（新）
- 新增 `order.status` enum：`pending` → `processing` → `waiting_finalization`／`failed` → `completed`／`cancelled`，取代舊二態 `PROCESSING`/`FAILED`
- `create_order` 清算改為兩段 DB transaction：stage 1（建單 + 既有券段清算），stage 2（新券段扣點發券後 update 併回同筆 order）
- 建單成敗回歸單一條件 `discount_amount > 0`（`waiting_finalization`），否則 `failed`
- 新券段失敗分兩類，皆不改變成敗判定：
  - 點數端失敗（treelife 扣點 fail/timeout）→ retry + 每日 cronjob 對帳（成功則退點、失敗不處理、仍 timeout 告警）
  - 我方失敗（扣點成功但發券寫入失敗）→ 孤兒點數，5xx 非預期錯誤、人工善後
- `batch_finalize_orders` 終結前置為 `order.status = waiting_finalization`；COMPLETED → `completed`、CANCELLED → `cancelled`

### Rotation / quota 規則
- `max_redemption_per_rotation`（campaign 屬性、計張數）→ `max_points_per_rotation`（**rotation 屬性**、跨品牌合計點數上限）
- `max_points_per_rotation` 與 `max_redemptions_per_order` 之值 `0` 一律代表無上限
- 跨品牌並發防超用機制移交 RD 技術規格，不在 API spec 範圍

### create_order 錯誤碼與檢查調整
- 移除 `MEMBER_EXCEED_PER_ORDER_QUOTA`（能進新券段即代表 per-order 未占滿，不存在此失敗情境）
- 移除前置 `BRAND_NOT_FOUND`：`brand_id` 不再前置存在性檢查，不存在/無效者於清算階段自然歸入 `NO_ACTIVE_CAMPAIGN`
- `AUTO_REDEEM_NOT_ENABLED_FOR_BRAND` → `AUTO_REDEEM_NOT_ENABLED`，釐清為**會員層級**（`members.auto_redeem_enabled`），品牌無獨立 auto disable
