---
title: Cronjob Spec - expire_coupon
permalink: /cronjob-specs/expire-coupon/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-20 | 初版建立：定義 `expire_coupon` 排程批次作業，將 DB 狀態仍為 `available` 但 `expired_at` 已過期之券，批次回壓為 `expired`。範圍界定為純狀態回壓，不含統計／通知／`consuming` 卡住回收；定案比照 `batch_finalize_orders` 既有 pattern，回壓時同步寫入 `coupon_event_logs`（`type=expired`），維持稽核軌跡與其他觸發路徑一致 |

# Cronjob: expire_coupon

## 目的

系統目前無主動掃描機制批次回壓已過期券的狀態（見 CLAUDE.md「Coupon 狀態 enum」），因此 DB 可能長期存在 `expired_at` 已早於當下時間、但 `status` 仍為 `available` 的券。所有即時 API（`get_coupon_detail`、`get_coupons` 等）與 `create_order` 清算邏輯皆已各自即時比對 `expired_at` 與當下時間，**本 job 不影響任何既有業務判斷的正確性**。

本 job 的價值純粹是資料衛生（housekeeping）：讓 `coupons.status` 欄位如實反映實際狀態，避免：
- 需要直接信任 `status` 欄位的場景（如未來 admin 後台查詢、報表、資料分析）誤判
- 每個新增的讀取路徑都必須重新實作一次「`status=available` 且 `expired_at` 未到期」的雙條件判斷，形成重複邏輯與遺漏風險

## 執行時機

- 排程：每日一次，`00:00` 後盡快執行；建議 `00:10`（UTC+8），保留短暫緩衝以避開日切前後其他排程作業
  - 確切分鐘數屬執行環境調度細節，可由 RD／維運排程系統決定，不影響業務邏輯結果
  - 與既有「每日 04:00 cronjob」（`create_order` 扣點逾時對帳，見 `create_order.md`）為兩支獨立、互不依賴的排程，職責不同不合併
- 非 request-driven，無外部呼叫方觸發；不適用 `/coupon/...` `/bank/...` API 的 API Key／IP 白名單驗證機制

## 篩選條件

```
coupons.status = 'available' AND coupons.expired_at < now()
```

時間比對邊界（嚴格小於，非小於等於）與現行各 API 即時判斷「已過期」的邏輯一致（見 `get_coupon_detail.md`「status 顯示邏輯」：「`expired_at` 已早於當下時間」）。

## 動作

對每一筆符合篩選條件的 coupon：
- `status`：`available` → `expired`
- `updated_at`：更新為執行當下時間（比照現有慣例「狀態轉換時更新」，見 `get_coupons.md`）
- 新增一筆 `coupon_event_logs`（`type=expired`）

### coupon_event_logs 稽核紀錄（已定案）

`batch_finalize_orders` 的 `cancel`／`revoke` 流程中，`consumed` 券依到期與否轉為 `available` 或 `expired` 時，會各自新增一筆 `coupon_event_logs`（轉為 `expired` 者 `type=expired`）。本 job 比照此既有 pattern，回壓為 `expired` 時同步寫入同類型 log，避免「同樣轉為 `expired` 的券，依觸發路徑不同、稽核軌跡完整度不一致」——事後可單純從 `coupon_event_logs` 判斷任一張券何時、經由何種路徑變成 `expired`，不因觸發來源是本 job 或 `batch_finalize_orders` 而有落差。

## 實作限制與併發考量

- **必須為單一條件式 `UPDATE ... WHERE status='available' AND expired_at < now()`，不得先 `SELECT` 出候選清單再逐筆 `UPDATE`。** 理由：`create_order` 既有券段 FIFO 選券時，可能在同一時間窗把即將到期的券由 `available` 轉為 `consuming`（見 CLAUDE.md「`consuming`」說明）。若本 job 採「先讀後寫」，可能覆蓋掉這個並發轉換；改用條件式 `UPDATE`，一旦某筆券已搶先被轉為 `consuming`，`WHERE` 條件即不再命中，該筆自然跳過——等同這張券在到期前一刻被使用，屬正常 FIFO 結果，不是需要處理的例外
- 若單次符合條件筆數過大，建議比照 `batch_finalize_orders` 既有的 chunk 處理模式分批 commit（例如以 id 範圍分段），避免單一長交易鎖表影響其他即時寫入（如 `create_order`）
- Job 具備天然冪等性：已轉為 `expired` 的券不再符合 `WHERE` 條件，重複執行無副作用；若某次執行中途失敗，下次排程重跑會自然補齊未處理完的部分，不需要額外的執行紀錄表或 checkpoint 機制

## 範圍排除（Out of Scope）

- **不處理卡在 `consuming` 的券**：`create_order` stage 2 若在最終 transaction 前中斷，既有券可能卡在 `consuming` 無法自然轉出。此為另一獨立的待補充回收機制（見 CLAUDE.md「Coupon 狀態 enum」`consuming` 說明，與 `order.status=pending` 滯留問題同性質同批次處理），不在本 job 範圍內
- **不產生任何統計數據、報表或下游通知**（如即將到期提醒）。如未來有此需求，屬另案規格，不隨本 job 附帶實作
- **不影響 `consumed`／`settled`／`voided` 券**：這些狀態皆有各自專責的轉換流程（`batch_finalize_orders`、人工注銷 CLI 等）或已是終態，本 job 篩選條件天然不會命中

## 待確認：監控與失敗處理

以下細節目前尚無定案，列出供你確認：
- 執行失敗（DB 連線中斷、chunk 中途失敗等）的告警機制與重試策略——是否比照現行「每日 04:00 cronjob」的告警管道？目前文件中未定義該管道的具體實作細節，需另外確認後補上
- 是否需要記錄每次執行的處理筆數（本次 `available → expired` 更新了幾筆），供事後稽核執行是否正常；若需要，寫入位置（application log／監控系統）待定
