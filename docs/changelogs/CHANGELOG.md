# Changelog

<!-- changelog subagent 會在此處插入最新條目 -->

## 2026-07-09 — create_order / bank_get_order 新增 coupons[] 對帳明細

### 發卡主機對帳明細
- `create_order` 與 `bank_get_order` response 新增 `coupons[]` 陣列，列出本次訂單所用的所有券（含舊券與新券），兩支 API 同結構
- 每張券含 `is_new_issued`（是否本次訂單即時發行）、`discount_amount`、`redeem_points`，以及**本次**消耗之 `tree_points`/`cub_points` 點數拆分
- 舊券（`is_new_issued = false`）本次不扣點，`tree_points`/`cub_points` 固定為 `0`（歷史成本記於 `redeem_points`）
- `cub_points`（小樹點信用卡）為銀行發行點數，是發卡主機對帳的主要依據；`tree_points`（小樹點生活）為神坊端點數，一併列出供完整核對
- 對帳恆等式：`Σ coupons[].tree_points == points_used.tree_points`、`Σ coupons[].cub_points == points_used.cub_points`、`Σ coupons[].discount_amount == discount_amount`
- `bank_get_order` 提供事後批次對帳重查（明細與 `create_order` 建單當下回傳者一致）；`failed` 訂單 `coupons[]` 為空陣列、`points_used` 皆為 0

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
