# 券夾/券列表/訂單列表 效能調整方向 — SA 討論用 Plan

> 承接 [2026-07-17 效能討論彙整](2026-07-17-coupon-wallet-get-coupons-效能討論.md)，前端溝通後收斂三個方向，經 SA 討論後於 2026-07-22 完成最終定案與文件調整。

## 1. get_coupon_wallet — 重新定義為「所有操作過的品牌」（已定案並實作，2026-07-22）

**現況（調整前）**：品牌需符合「過去 366 天（T-366，含）內有 coupon 發行紀錄」才列入清單；`available_coupon_count` 僅聚合 `available` 張數。

**最終決議**：
- 拿掉 366 天門檻，品牌清單不限時間，只要曾經有過 coupon 發行紀錄即列出
- `available_coupon_count` 聚合口徑擴大為 `available` + `consumed`（尚可用或使用中皆計入），取代原本僅計 `available` 的邏輯
- `get_coupons` **不加任何時間窗**，維持不限時間；不採用先前規劃的「僅顯示近一年」免責文字（見下方原因）——因為 `get_coupon_wallet` 拿掉時間限制的目的就是讓用戶找到「很久以前操作過的品牌」，若 `get_coupons` 卻用時間窗擋住會讓用戶點進去看到空列表，兩者矛盾

**已完成調整：**
- `get_coupon_wallet.md`：功能說明／使用情境／邏輯說明移除所有「過去一年內」字眼；品牌入列條件改為「該品牌下存在任一 coupon（不限時間、不限狀態）」；`available_coupon_count` 說明改為聚合 `available` + `consumed`
- PRD：§二 Coupon Wallet 規則、Flow 6 品牌摘要段落同步修正
- 兩份文件 Changelog、共用 `CHANGELOG.md` 已各補一筆

## 2. get_coupons — 改為三個獨立列表，維持四態不變（已定案並實作，2026-07-22）

**現況（調整前）**：兩個頁籤——待折抵（`AVAILABLE` + `CONSUMED`）／紀錄（`SETTLED` + `EXPIRED`）。紀錄頁籤內 `SETTLED` 依 `updated_at DESC`、`EXPIRED` 依 `expired_at DESC`，排序欄位不同，是效能疑慮的根源。

> ⚠️ 本節先前曾記錄「SA 建議收斂為三態 `available`/`used`/`expired`，禁止自由組合」的方向，**最終未採用**，改為維持原始四態、僅調整前端呈現方式（見下）。

**最終決議**：狀態 enum 維持四態不變（`available`/`consumed`/`settled`/`expired`），`status[]` 維持可複選陣列，不限制自由組合。前端呈現方式改為三個獨立列表：
- **待折抵**：查詢 `status[]=available,consumed`——兩者排序欄位相同（皆為 `expired_at`），合併查詢不影響效能
- **已折抵**：查詢 `status[]=settled`（單一狀態，依 `updated_at DESC` 排序）
- **已過期**：查詢 `status[]=expired`（單一狀態，依 `expired_at DESC` 排序）

因為 `settled` 與 `expired` 現在分屬不同列表、各自單獨查詢，**不需要**強制統一排序鍵——排序鍵不同的問題本質上是「兩個原本合併查詢的狀態改成分開查詢」自然解決的，不需要靠合併狀態值或限制參數組合來處理。

**已完成調整：**
- `get_coupons.md`：使用情境新增三個獨立列表的說明與對應查詢方式；邏輯說明補充「`settled`／`expired` 排序欄位不同，前端不應合併查詢」提醒
- PRD：Flow 6 券列表段落同步修正
- 兩份文件 Changelog、共用 `CHANGELOG.md` 已各補一筆

## 3. get_member_orders — 維持 coupon_usage_summary，改為建單當下寫入快照（已定案並實作）

**現況（調整前）**：`coupon_usage_summary[]` 由後端依 `campaign_name` + `is_new_issued` 做 GROUP BY 聚合後回傳（分組後的摘要列，含 `quantity`）；另有訂單層級 `point_used` 彙總欄位（本次新發券消耗點數加總）；兩者皆於 `get_member_orders` 查詢當下即時運算。

**決議方向（已定案，取代先前「拆成兩支 API」與「攤平交前端彙總」兩個選項）**：不拆 API、不攤平成逐張明細，`get_member_orders` 的 response 結構完全不變；改為在 `create_order` 建單完成當下，就把 `coupon_usage_summary`（依 `campaign_name` + `is_new_issued` 分組）與 `point_used` 計算好，寫入該筆 order 記錄（快照），`get_member_orders` 直接讀快照回傳，不再即時 JOIN／GROUP BY。

**這個方向同時解決了原本兩個顧慮：**
- 效能：聚合運算從「每次列表查詢都算 20 筆訂單」搬到「每筆訂單建立時只算一次」，讀取路徑變成單表查詢
- Payload 過大：維持分組後的彙總結構（而非逐張攤平），單筆訂單即使用了 20 張券，回傳的仍是精簡的分組列表，不會膨脹成逐張明細

**已完成調整：**
- `create_order.md`：新增「`get_member_orders` 用券摘要快照」段落，說明建單完成時同步寫入 `coupon_usage_summary`／`point_used` 快照
- `get_member_orders.md`：邏輯說明補充「讀取快照、不即時聚合」，response 結構不變
- 兩份文件 Changelog、共用 `CHANGELOG.md` 已各補一筆
- PRD 未描述這支 API 的 response 欄位細節，不需修改本文

---

## 待辦

三點皆已定案並完成文件調整，無待辦事項。
