# 券夾/券列表/訂單列表 效能調整方向 — SA 討論用 Plan

> 承接 [2026-07-17 效能討論彙整](2026-07-17-coupon-wallet-get-coupons-效能討論.md)，前端溝通後已收斂三個方向。本文件列出對應要調整的文件/欄位，以及送到 SA 討論前建議先釐清的開放問題。**尚未定案，待 SA 討論後才進入實際編修。**

## 1. get_coupon_wallet — 重新定義為「所有操作過的品牌」（SA 已確認）

**現況**：品牌需符合「過去 366 天（T-366，含）內有 coupon 發行紀錄」才列入清單；`available_coupon_count` 本身已不受此時間窗限制。

**決議方向（SA 確認）**：拿掉 366 天門檻，重新定義為「所有操作過的品牌、對應可用券」——品牌清單不限時間，只要曾經有過 coupon 發行紀錄即列出；`available_coupon_count` 維持現行邏輯（僅聚合目前 `AVAILABLE` 張數）不變。

**需要調整：**
- `get_coupon_wallet.md`：功能說明／使用情境／邏輯說明中所有「過去一年內（T-366 天，含）」字眼移除；品牌入列條件改為「該品牌下存在任一 coupon（不限時間、不限狀態）」；`brands: []` 空清單條件說明由「過去一年內無任何品牌換券紀錄」改為「從未有過任何 coupon 發行紀錄」；查詢邏輯由「`member_id + created_at` 範圍過濾」簡化為「`member_id` 下 DISTINCT `brand_id`」等值查詢
- PRD：§二 Coupon Wallet 概念/規則、Flow 6 品牌摘要段落（`docs/樹配券2.0_PRD.md:462`）同步移除「過去一年內」敘述
- 兩份文件的 Changelog、共用 `CHANGELOG.md` 各補一筆

**⚠️ 重要修正（回應 SA 提出的體感衝突）：`get_coupons` 不應加任何時間窗，CR 原規劃的「僅顯示近一年樹配券紀錄」免責文字建議取消。**

理由：`get_coupon_wallet` 拿掉時間限制的目的，就是讓用戶能找到「很久以前操作過的品牌」；如果 `get_coupons` 卻用一年時間窗擋住，等於讓用戶點進去看到空列表，wallet 卡片的存在意義被架空，兩者互相矛盾。最初會想幫 `get_coupons` 加時間窗，是為了緩解「SETTLED 依 `updated_at`、EXPIRED 依 `expired_at` 排序鍵不同、索引無法滿足」的效能疑慮——但這個根本問題已經被下方第 2 點的新分組方式解決（見下），時間窗只是妥協手段，問題解決後就不再需要，也不該為了不存在的效能理由犧牲功能完整性。建議 `get_coupons` 維持真正不限時間，讓 wallet 內任何品牌點進去都保證看得到資料。

## 2. get_coupons — status 重新分組為三態，禁止自由組合（SA 已確認，附排序鍵建議）

**現況**：兩個頁籤——待折抵（`AVAILABLE` + `CONSUMED`）／紀錄（`SETTLED` + `EXPIRED`）。紀錄頁籤內 `SETTLED` 依 `updated_at DESC`、`EXPIRED` 依 `expired_at DESC`，排序欄位不同，是效能疑慮的根源。

**決議方向（SA 確認，取代原本「拆三個列表」的分組方式）**：對前端回覆與查詢用的 `status` 重新定義為三態——`available`（原 `AVAILABLE`）、`used`（原 `CONSUMED` + `SETTLED` 合併）、`expired`（原 `EXPIRED`）；且**不能自由搭配組合**，每次呼叫只能指定其中一種，不再是可複選的 `status[]`。

**建議的排序鍵設計（解決原本混合排序鍵問題的關鍵）：**
- `available`：依 `expired_at DESC` 排序（沿用原 `AVAILABLE` 邏輯）
- `used`（`CONSUMED` + `SETTLED`）：**統一依 `updated_at DESC` 排序**——對 `CONSUMED` 而言 `updated_at` 即「成立訂單、轉入使用中的時間」，對 `SETTLED` 而言即「核銷時間」，兩者語意上都是「這張券最近一次狀態變動的時間」，可視為同一概念，合併後不再有排序鍵不一致的問題
- `expired`：依 `expired_at DESC` 排序（沿用原 `EXPIRED` 邏輯）

三個 bucket 各自單一排序鍵，`(member_id, brand_id, status, sort_column)` 一組複合索引即可滿足查詢，不需要 filesort，原本的效能疑慮從根本解決（不是靠限制資料量，而是排序鍵本身不再衝突）。

**需要調整：**
- `get_coupons.md`：
  - `status[]`（可複選陣列）改為單值 `status`（`available` \| `used` \| `expired`），Request Parameters 表格同步修改
  - Response 每筆券的 `status` 欄位回傳值同步改為這三個新值（不再回傳原始 `AVAILABLE`/`CONSUMED`/`SETTLED`/`EXPIRED`）
  - 排序規則段落改為上述三態各自對應的排序鍵
  - 使用情境／邏輯說明中「前端以待折抵／紀錄兩頁籤呈現」改為「前端以 `available`／`used`／`expired` 三個列表呈現，各自對應單一 `status` 值查詢」
- PRD：Flow 6 券列表段落（`docs/樹配券2.0_PRD.md:464`）「兩頁籤」敘述改為新的三態定義
- 兩份文件的 Changelog、共用 `CHANGELOG.md` 各補一筆

**建議跟 SA 確認的問題：**
1. `get_coupon_detail.md`（單張券詳情）的 `status` 欄位是否也要跟著收斂成三態，還是維持原本 `AVAILABLE`/`CONSUMED`/`SETTLED`/`EXPIRED` 四態？單張詳情頁面使用者可能需要精確分辨「折抵處理中（CONSUMED）」vs「已核銷完成（SETTLED）」，建議維持原始四態，僅在**列表**層級做三態收斂，但需要跟 SA/前端確認這個顆粒度差異是否會造成困惑
2. CLAUDE.md／PRD 目前定義的 coupon 狀態機是四態（`AVAILABLE`→`CONSUMED`→`SETTLED`/`EXPIRED`），這是系統內部與其他 API（如 `create_order`、`get_coupon_detail`）共用的權威定義；本次三態只限定在 `get_coupons` 這支 API 的呈現層，需要在文件中明確註明「僅此 API 的顯示層收斂，不影響底層狀態機」，避免未來誤植成全域改動

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
