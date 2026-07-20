# 券夾/券列表/訂單列表 效能調整方向 — SA 討論用 Plan

> 承接 [2026-07-17 效能討論彙整](2026-07-17-coupon-wallet-get-coupons-效能討論.md)，前端溝通後已收斂三個方向。本文件列出對應要調整的文件/欄位，以及送到 SA 討論前建議先釐清的開放問題。**尚未定案，待 SA 討論後才進入實際編修。**

## 1. get_coupon_wallet — 移除時間限制

**現況**：品牌需符合「過去 366 天（T-366，含）內有 coupon 發行紀錄」才列入清單；`available_coupon_count` 本身已不受此時間窗限制。

**決議方向**：拿掉 366 天門檻，品牌清單改為「不限時間，只要曾經有過 coupon 發行紀錄即列出」；CR 會在 `get_coupons`（單一品牌券一覽）UI 加註文字「僅顯示近一年樹配券紀錄」，降低「券夾出現品牌、點進去卻無資料」的體感落差。

**需要調整：**
- `get_coupon_wallet.md`：功能說明／使用情境／邏輯說明中所有「過去一年內（T-366 天，含）」字眼移除；品牌入列條件改為「該品牌下存在任一 coupon（不限時間、不限狀態）」；`brands: []` 空清單條件說明由「過去一年內無任何品牌換券紀錄」改為「從未有過任何 coupon 發行紀錄」；查詢邏輯由「`member_id + created_at` 範圍過濾」簡化為「`member_id` 下 DISTINCT `brand_id`」等值查詢
- PRD：§二 Coupon Wallet 概念/規則、Flow 6 品牌摘要段落（`docs/樹配券2.0_PRD.md:462`）同步移除「過去一年內」敘述
- 兩份文件的 Changelog、共用 `CHANGELOG.md` 各補一筆

**建議跟 SA 確認的問題：**
1. 拿掉時間限制後，`brands` 清單理論上會隨會員使用年限單調增加、不會再縮減；即使查詢本身簡化為等值查詢，仍建議請 SA 確認實務資料量級（例如長年高頻換多品牌的會員）下是否有其他隱憂
2. CR 的免責文字只解決「品牌不會從券夾消失」，**沒有解決「點進去可能是很久以前的舊資料」這個體感問題本身**——`get_coupons` 目前並未搭配任何時間窗（本次調整方向 2 也未涉及此點），這裡的落差是靠 UI 文案管理期待，而非資料一致；建議跟 SA 確認這樣的產品決策是否已經足夠，或者要不要在 `get_coupons` 也同步討論時間窗（此為 2026-07-17 文件中「加時間窗」選項，本次前端溝通並未提及是否採用）

## 2. get_coupons — 拆成三個獨立列表

**現況**：兩個頁籤——待折抵（`AVAILABLE` + `CONSUMED`）／紀錄（`SETTLED` + `EXPIRED`）。紀錄頁籤內 `SETTLED` 依 `updated_at DESC`、`EXPIRED` 依 `expired_at DESC`，排序欄位不同，是效能疑慮的根源。

**決議方向**：CR 改為三個獨立列表——待折抵（`AVAILABLE` & `CONSUMED`）、已折抵（`SETTLED`）、已過期（`EXPIRED`），對應 2026-07-17 文件中的「拆子列表」選項。

**需要調整：**
- `get_coupons.md`：使用情境／邏輯說明中「前端以待折抵／紀錄兩頁籤呈現」改為「前端以待折抵、已折抵、已過期三個列表呈現，各自對應固定的 `status[]` 組合呼叫」；排序規則本身不需改變（各 bucket 排序邏輯已存在），但需補充「前端固定三個獨立呼叫，不會再出現 `status[]` 橫跨 `SETTLED` 與 `EXPIRED` 的查詢情境，混合排序鍵疑慮隨之解除」；`status[]` 參數定義本身不需變動
- PRD：Flow 6 券列表段落（`docs/樹配券2.0_PRD.md:464`）「兩頁籤」敘述改為「三個列表」
- 兩份文件的 Changelog、共用 `CHANGELOG.md` 各補一筆

**建議跟 SA 確認的問題：**
1. `status[]` 參數本身是否要保留「可自由跨 bucket 組合」的彈性（含理論上仍可傳 `SETTLED,EXPIRED`），還是要在文件中明確限制/警示不建議這樣呼叫？若保留彈性但不限制，效能疑慮只是「前端目前不這樣用」，並未真正在 API 層解決，建議請 SA 定調文件要「建議」還是「強制」

## 3. get_member_orders — 不拆 API，張數/點數加總交由前端處理

**現況**：`coupon_usage_summary[]` 由後端依 `campaign_name` + `is_new_issued` 做 GROUP BY 聚合後回傳（分組後的摘要列，含 `quantity`）；另有訂單層級 `point_used` 彙總欄位（本次新發券消耗點數加總）。

**決議方向**：不採用「拆成訂單列表 + 單筆用券明細」兩支 API 的方案；改為將 `coupon_usage_summary` 攤平成逐張券明細，由前端自行加總（張數、金額等），對應 2026-07-17 文件中的「攤平交前端彙總」選項。

**需要調整：**
- `get_member_orders.md`：
  - Response schema：`coupon_usage_summary[]`（分組彙總）改為逐張明細陣列（暫定命名 `coupons_used[]`），每筆對應一張券，欄位含 `campaign_name`、`is_new_issued`、`discount_amount`（該張）、`tree_points`/`cub_points`（該張；`is_new_issued = true` 為本次消耗，`false` 為該券**原始發行時**的歷史組成，比照 `create_order.md` 的 `existing` 欄位定義方式，需在 spec 中明確標註避免前端誤解為本次消耗）
  - 訂單層級 `point_used` 彙總欄位：因前端現在可自行從逐張明細加總，是否還要保留這個方便欄位待 SA/前端確認（見下方開放問題）
  - Sample JSON、Response items 表格、邏輯說明段落同步改寫
  - Changelog 補一筆
- PRD：目前 PRD 並未描述 `get_member_orders` 的 response 欄位細節（僅泛稱「摘要列表」），故不需要額外修改 PRD 本文
- 共用 `CHANGELOG.md` 補一筆

**建議跟 SA 確認的問題：**
1. 逐張明細會讓單筆訂單的資料筆數變多（例如一張訂單用了 10 張同 campaign 的券，現在是 1 筆彙總列，之後變成 10 筆明細）；對單一會員訂單量大、每筆訂單又用很多張券的極端 case，需要請 SA 評估單頁 response payload 大小是否可接受
2. 訂單層級 `point_used` 是否保留？保留的話後端仍需做一次簡單 `SUM`（並未完全去除聚合運算，只是從 GROUP BY 換成單純加總）；不保留則前端每個訂單都要自行跑一次加總邏輯——需要確認前端畫面是否真的需要顯示這個彙總數字

---

## 待辦（SA 討論後）

三個方向 SA 確認沒有疑慮後，再依上述「需要調整」清單逐一修改對應 API spec、PRD、changelog，並個別 commit。
