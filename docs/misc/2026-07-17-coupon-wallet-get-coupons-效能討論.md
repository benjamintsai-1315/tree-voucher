# get_coupon_wallet / get_coupons / get_member_orders 效能討論項目彙整

> 供會議討論用，彙整目前針對 `get_coupon_wallet.md`、`get_coupons.md`、`get_member_orders.md` 識別出的效能疑慮，以及可能的因應方向。皆為討論項目，尚未定案。

| 討論項目 | 建議原因 | 對效能的影響幅度 |
| --- | --- | --- |
| 【get_coupons】紀錄頁籤拆成兩個子列表（已折抵完成 / 已過期，各自呈現，不合併排序） | SETTLED 依 `updated_at DESC`、EXPIRED 依 `expired_at DESC`，兩者排序欄位不同，B-tree 索引無法對同一查詢中不同 row 用不同排序欄位直接產出結果；拆開後每個 bucket 各自單一排序鍵，可直接命中各自索引，不需 filesort | **高** —— 徹底解決混合排序鍵問題；仍需搭配「加時間窗」項目才能限制資料規模隨時間增長 |
| 【get_coupons】紀錄頁籤維持合併列表，但排序欄位統一（皆改依 `expired_at DESC`，放棄 SETTLED 依核銷時間排序） | 用單一排序欄位取代「依狀態切換排序欄位」邏輯，一個複合索引 `(member_id, brand_id, status, expired_at)` 即可滿足，不需 filesort 或 union 兩個查詢 | **高** —— 效能面與拆子列表相當，但是用犧牲「SETTLED 依核銷時間排序」這個既有決策換來的，屬產品取捨而非純工程優化 |
| 【get_coupons】紀錄頁籤加上預設時間窗（比照 `get_coupon_wallet` 的 T-366 天） | 不解決排序鍵不同的根本問題，但限制單次查詢/排序的資料規模上限，避免長年活躍用戶的資料無限增長 | **中** —— 緩解資料量無限增長的風險；排序鍵不同的問題仍在，只是規模變小 |
| 【get_coupon_wallet】拿掉 366 天時間限制 | 目前用「品牌是否有 coupon 落在過去 366 天內」決定是否列出，需要 `member_id + created_at` 範圍過濾再 GROUP BY；拿掉後只需要 `member_id` 底下 DISTINCT `brand_id`，等值查詢取代範圍查詢，索引更單純（`(member_id, brand_id)` 即可）；同時修正一個潛在的資料矛盾——若 `coupon_valid_days` 設定夠長，可能出現「券仍是 AVAILABLE、但因發券時間超過 366 天而品牌不顯示」的邏輯漏洞 | **中** —— 查詢從範圍過濾簡化為等值查詢，效能有感提升，但主要效益其實是「邏輯更正確」，而非效能本身 |
| 【get_coupon_wallet】只呈現有 available 的品牌 | 把「品牌清單」與「available 張數」兩個聚合合併成一個：直接對 available coupon 做 `GROUP BY brand_id HAVING COUNT > 0`，不需另外查「過去有無任何紀錄」；索引只需要 `(member_id, status, brand_id)` 一組 | **高** —— 直接砍掉一半的查詢邏輯（不需歷史品牌查詢）；但 0 張可用券的品牌會從摘要消失，使用者將失去瀏覽該品牌歷史券的入口（除非另開通路） |
| 【get_coupon_wallet】依 brands 分拆的必要性（`get_coupon_wallet` 這支 API 存在的必要性） | 若不需要分品牌瀏覽，整支 `get_coupon_wallet`（連同上述兩點的所有查詢邏輯）可直接移除，前端改用 `get_coupons` 搭配品牌篩選/顯示即可 | **最高** —— 直接消除問題源頭；但屬資訊架構層級的改動，需前端/設計重新確認畫面流程（品牌卡片 → 分品牌瀏覽的既有設計） |
| 【get_member_orders】把訂單列表與券使用明細拆成兩隻 API | 目前每次列表查詢（分頁 20 筆訂單）都要對每筆訂單一併 JOIN + GROUP BY（依 `campaign_name` + `is_new_issued`）計算 `coupon_usage_summary`／`point_used`；但使用者未必會點開每一筆訂單看用券明細。拆成「訂單列表」（純 `orders` 表查詢，不需 JOIN）＋「單筆訂單用券明細」（點開時才查，只需對 1 筆 order 做 JOIN/聚合）兩支 API，可把聚合成本從「每次列表都算 20 筆」降為「使用者實際點開才算 1 筆」 | **高** —— 列表查詢從「JOIN + 20 筆聚合」降為單表查詢，分頁滾動情境效益明顯；代價是查看單筆明細需多一次 API call，且屬資訊架構調整，需前端配合畫面設計 |
| 【get_member_orders】券使用明細攤平為逐張券明細，交由前端自行彙總 | 現行 `coupon_usage_summary` 由後端依 `campaign_name` + `is_new_issued` 做 GROUP BY 聚合後回傳；若改成直接回傳該訂單用到的每一張券（含 `campaign_name`、`is_new_issued`、`discount_amount`、點數等逐張欄位），後端只需單純 JOIN 撈資料，不需 GROUP BY 運算，把彙總成本轉嫁到前端（單筆訂單資料量小，運算成本可忽略） | **中** —— 省去後端 GROUP BY 運算成本，但換來單筆訂單回傳的資料筆數變多（逐張券 vs 分組後的摘要列），且彙總邏輯（依 campaign＋新舊分組加總）從後端搬到前端，未來分組規則異動時前後端須同步調整，增加維護與一致性風險 |

---

**共通脈絡**：所有項目的邏輯一致——透過「限縮查詢範圍」「省略提前聚合」「拆分關注點」換取查詢效能，但代價分別是：產品功能縮減（歷史瀏覽入口、既有排序語意）、多一次 API 呼叫、或把彙總邏輯與維護責任轉移到前端。需要在會議上逐項確認能否接受對應代價。

---

## 最終決議（2026-07-22）

- **get_coupons 紀錄頁籤拆成兩個子列表** → ✅ 採用，實際定案為改成三個獨立列表（待折抵／已折抵／已過期）；因 `settled`／`expired` 各自單一查詢、單一排序欄位，**不需要**額外統一排序鍵
- **get_coupons 排序欄位統一** → ❌ 不採用，維持各狀態原本排序欄位（`settled` 依 `updated_at`、其餘依 `expired_at`）
- **get_coupons 加時間窗** → ❌ 不採用，維持不限時間
- **get_coupon_wallet 拿掉 366 天限制** → ✅ 採用，品牌清單不限時間
- **get_coupon_wallet 只呈現有 available 的品牌** → ❌ 不採用；品牌清單維持顯示所有曾操作過的品牌（含 0 張可用），改為 `available_coupon_count` 聚合口徑擴大為 `available` + `consumed`
- **get_coupon_wallet 依 brands 分拆的必要性** → ❌ 不採用，維持獨立 API
- **get_member_orders 拆分 API** → ❌ 不採用
- **get_member_orders 攤平交前端彙總** → ❌ 不採用；最終改為「`create_order` 建單當下計算並寫入快照，`get_member_orders` 直接讀取」（2026-07-21 另行定案），非本文件原列的兩個選項
