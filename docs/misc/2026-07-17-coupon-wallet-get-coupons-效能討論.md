# get_coupon_wallet / get_coupons 效能討論項目彙整

> 供會議討論用，彙整目前針對 `get_coupon_wallet.md`、`get_coupons.md` 識別出的效能疑慮，以及可能的因應方向（含 SA 建議）。皆為討論項目，尚未定案。

## 一、get_coupons.md ——「紀錄」頁籤（SETTLED + EXPIRED 合併排序）

背景：目前排序規則為 `AVAILABLE`/`CONSUMED`/`EXPIRED` 依 `expired_at DESC`，但 `SETTLED` 依 `updated_at DESC`（finalize 時間）。「紀錄」頁籤同時查詢 `SETTLED` + `EXPIRED`，兩者排序欄位不同。

| 討論項目 | 我們建議的原因 | 對效能的影響幅度 |
| --- | --- | --- |
| **A. 紀錄頁籤拆成兩個子列表**（已折抵完成 / 已過期，各自呈現，不合併排序） | SETTLED、EXPIRED 排序欄位不同，B-tree 索引無法對同一查詢中不同 row 用不同排序欄位直接產出結果；拆開後每個 bucket 各自單一排序鍵，可直接命中各自索引，不需 filesort | **高** —— 徹底解決混合排序鍵問題；仍需搭配 C 才能限制資料規模隨時間增長 |
| **B. 紀錄頁籤維持合併列表，但排序欄位統一**（皆改依 `expired_at DESC`，放棄 SETTLED 依核銷時間排序） | 用單一排序欄位取代「依狀態切換排序欄位」邏輯，一個複合索引 `(member_id, brand_id, status, expired_at)` 即可滿足，不需 filesort 或 union 兩個查詢 | **高** —— 效能面與 A 相當，但是用犧牲「SETTLED 依核銷時間排序」這個既有決策換來的，屬產品取捨而非純工程優化 |
| **C. 紀錄頁籤加上預設時間窗**（比照 `get_coupon_wallet` 的 T-366 天） | 不解決排序鍵不同的根本問題，但限制單次查詢/排序的資料規模上限，避免長年活躍用戶的資料無限增長 | **中** —— 緩解資料量無限增長的風險；排序鍵不同的問題仍在，只是規模變小 |

## 二、get_coupon_wallet.md（SA 建議）

| 討論項目 | 我們建議的原因 | 對效能的影響幅度 |
| --- | --- | --- |
| **1. 拿掉 366 天時間限制** | 目前用「品牌是否有 coupon 落在過去 366 天內」決定是否列出，需要 `member_id + created_at` 範圍過濾再 GROUP BY；拿掉後只需要 `member_id` 底下 DISTINCT `brand_id`，等值查詢取代範圍查詢，索引更單純（`(member_id, brand_id)` 即可）；同時修正一個潛在的資料矛盾——若 `coupon_valid_days` 設定夠長，可能出現「券仍是 AVAILABLE、但因發券時間超過 366 天而品牌不顯示」的邏輯漏洞 | **中** —— 查詢從範圍過濾簡化為等值查詢，效能有感提升，但主要效益其實是「邏輯更正確」，而非效能本身 |
| **2. 只呈現有 available 的品牌** | 把「品牌清單」與「available 張數」兩個聚合合併成一個：直接對 available coupon 做 `GROUP BY brand_id HAVING COUNT > 0`，不需另外查「過去有無任何紀錄」；索引只需要 `(member_id, status, brand_id)` 一組 | **高** —— 直接砍掉一半的查詢邏輯（不需歷史品牌查詢）；但 0 張可用券的品牌會從摘要消失，使用者將失去瀏覽該品牌歷史券的入口（除非另開通路） |
| **3. 依 brands 分拆的必要性**（`get_coupon_wallet` 這支 API 存在的必要性） | 若不需要分品牌瀏覽，整支 `get_coupon_wallet`（連同上述兩點的所有查詢邏輯）可直接移除，前端改用 `get_coupons` 搭配品牌篩選/顯示即可 | **最高** —— 直接消除問題源頭；但屬資訊架構層級的改動，需前端/設計重新確認畫面流程（品牌卡片 → 分品牌瀏覽的既有設計） |

---

**共通脈絡**：由上到下（A→C、1→3）simplification 幅度遞增，效能/複雜度收益也遞增，但砍掉的產品功能（歷史瀏覽入口、品牌卡片視覺、既有排序語意）也隨之遞增，需要在會議上逐項確認產品端能否接受對應代價。
