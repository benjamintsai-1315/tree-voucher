# Changelog

<!-- changelog subagent 會在此處插入最新條目 -->

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
