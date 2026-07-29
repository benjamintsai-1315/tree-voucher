# Changelog

<!-- changelog subagent 會在此處插入最新條目 -->

## 2026-07-29 — 全系統 API response 時間精度盤點：統一補齊毫秒精度

- 盤點所有現行 API spec（`docs/api/`，排除已廢除的 `get_order.md`/`finalize_order.md`/`update_member_settings.md`）的 response 時間欄位，統一補上「毫秒精度」說明與 Sample 的 `.000`（或既有 `.999` 日界值不變）
- 修正欄位涵蓋：`bank_get_order.md`（`finalized_at`/`created_at`）、`get_current_rotation.md`（`start_time`/`end_time`、品牌與 campaign 的 `created_at`/`updated_at`；`end_time` 確認為日界，維持 `23:59:59.999` 與 `expired_at` 精度規則一致）、`get_finalize_batch_status.md`（`submitted_at`/`completed_at`/`finalized_at`）、`get_member_orders.md`（`finalized_at`/`created_at`）、`get_member_settings.md`（`last_brand_selection_changed_at`）、`get_member_settings_change_logs.md`（`created_at`）
- **例外**：`get_member_orders.md`／`create_order.md` 的 `transaction_time` 為發卡主機提供之原樣值（passthrough，不參與清算），精度依發卡主機原始輸入，本系統不強制補齊毫秒，排除於本次盤點範圍
- `get_coupons.md`、`get_coupon_detail.md`、`create_order.md`（既有的 `created_at`/`expired_at`）先前已具備正確的毫秒精度，本次未變動

## 2026-07-29 — get_member_orders 新增 campaign_discount_amount，分組鍵擴充

- `coupon_usage_summary[]` 新增 `campaign_discount_amount`（該 campaign 定義之單張券折抵金額，coupon 建立時快照，語意與 `get_coupon_detail.discount_amount` 一致）
- `campaign_name` 範例值改為不含金額的泛用名稱（如「樹配券」），實際折抵金額由 `campaign_discount_amount` 另外提供，由前端自行組成顯示字串（如「樹配券 20」）
- 分組鍵由 `campaign_id`+`campaign_name` 擴充為 `campaign_id`+`campaign_name`+`campaign_discount_amount`：`campaign_discount_amount` 與 `campaign_name` 同為 coupon 建立時的快照值，若 campaign 事後調整折抵金額，同一 `campaign_id` 底下不同批次發行的券可能對應不同的 `campaign_discount_amount`，需一併納入分組鍵才不會被誤合併成一筆
- 已同步更新 `get_member_orders.md`（Sample、Response items、邏輯說明）、`create_order.md`（「`get_member_orders` 用券摘要快照」段落）

## 2026-07-27 — Coupon 狀態機新增 consuming 中間態（create_order 一致性修正）

- **背景**：`create_order` 既有券於流程一開始即被 FIFO 選定，但扣點需呼叫外部 treelife-api（無法納入 DB transaction rollback），新券也是扣點成功後才建立。若選定當下就直接標記 `consumed`，後續扣點或建券發生非預期錯誤時，會產生「訂單未完成、券卻已被視為用掉」的不一致
- **設計**：新增 `consuming` 為 coupon 狀態機的內部中間態：既有券於 FIFO 選定時、新券於扣點成功建立時，皆先標記 `consuming`；待新券段結果確定後，stage 2 結尾執行**最終 transaction**，將涉及的既有券＋新券一併由 `consuming` 轉為 `consumed`，同時 `order.status` 由 `pending` 轉為 `processing`/`error`，確保「券被視為用掉」與「訂單被視為成功」永遠綁定同一次 commit
- **前台可見性**：`consuming` 純屬內部狀態，`get_coupons`／`get_coupon_detail`／`get_coupon_wallet` 一律將其顯示/計入為 `consumed`，不對前端揭露
- **已知缺口（待補充，不在本次範圍）**：若流程於最終 transaction 前中斷，`consuming` 的券將卡在該狀態，回收/收斂機制待補充，與既有的 `order.status = pending` 滯留問題（同樣缺乏自動收斂機制）屬同一類失敗視窗，將一併處理
- 已同步更新 CLAUDE.md（Coupon／Order 狀態 enum）、PRD（§二 Coupon 規則與狀態機表、§三 清算邏輯、§四 訂單生命週期，並補上先前遺漏的 `discount_amount`→`total_discount_amount` 命名統一）、`create_order.md`（既有券段／新券段步驟、兩段 transaction 邊界、changelog 表頭修復）、`get_coupons.md`、`get_coupon_detail.md`、`get_coupon_wallet.md`

## 2026-07-24（訂正）— get_member_orders 改回巢狀設計，取代同日稍早的攤平陣列改動

- 前一則變更記錄（見下方同日條目）將 `get_member_orders` 的用券摘要改為攤平陣列並更名 `coupon_summary`，過早定案；討論後最終結論改回**巢狀設計**：
  - 欄位名維持 `coupon_usage_summary`（不更名為 `coupon_summary`），避免與 `create_order` 既有的物件型 `coupon_summary` 同名混淆
  - 分組鍵為 `campaign_id`+`campaign_name`（沿用同日稍早已定案的 campaign 改名修正），同一組合下的新舊券合併為一筆，透過 `coupon_usage.new_issued`/`coupon_usage.existing` 兩個子物件呈現，前端不需自行合併同 campaign 的多筆資料
  - `tree_points`/`cub_points` 攤平為 `new_issued`/`existing` 內的同層欄位（不額外包一層 `used_points`）
  - 保留「`existing` 應呈現該券原始發行時的歷史點數、非恆零」的修正
  - 命名統一（`total_discount_amount`）、`campaign_name` 快照化等其餘決議不受影響，維持不變
- 已同步更新 `create_order.md`（「`get_member_orders` 用券摘要快照」段落）、`get_member_orders.md`

## 2026-07-24 — create_order/get_member_orders 回應結構定案：命名統一、campaign_name 快照化、get_member_orders 改回攤平陣列

- **命名統一**：`discount_amount` 在代表「加總」語意時一律更名為 `total_discount_amount`（`create_order`、`bank_get_order`、`get_member_orders` 頂層與 `coupon_summary` 內同步），「單張券」的 `discount_amount`（如 `get_coupons`/`get_coupon_detail`/`bank_get_order.coupons_used[]`）維持不變
- **`campaign_name` 新增為 coupon 建立時的快照欄位**（PRD §二 Coupon 規則 1）：快照後不隨 campaign 事後改名回溯變動；`get_coupons.md`、`get_coupon_detail.md` 同步補註
- **`get_member_orders` 的 `coupon_usage_summary` 重新設計為攤平陣列**，更名為 `coupon_summary`（⚠️ 與 `create_order` 的 `coupon_summary` 同名但結構不同：前者為陣列、後者為物件，兩者粒度不同，僅欄位命名巧合相同）：
  - 分組鍵改為 `campaign_id`+`campaign_name`+`is_new_issued` 三者組合，取代上次（2026-07-23）的 `campaign_id` 巢狀合併設計；只有實際使用到的組合才輸出一筆，不強制輸出全零 row
  - `tree_points`/`cub_points` 攤平為同層欄位，取代巢狀 `used_points`；同時修正先前「`existing` 恆為 0」的錯誤——`is_new_issued=false` 應呈現該券原始發行時的歷史點數組成，與 `create_order.coupon_summary.existing` 語意一致
  - 新增範例說明 campaign 改名情境：同一 `campaign_id` 若歷經改名，不同批次發行的券可能對應不同的 `campaign_name`，各自成一筆、不合併
- 已同步更新 `create_order.md`（含「`get_member_orders` 用券摘要快照」段落）、`get_member_orders.md`、`bank_get_order.md`、`get_coupons.md`、`get_coupon_detail.md`、PRD（§二 Coupon 規則）

## 2026-07-23 — 新增客服/營運人工注銷 Coupon 機制（CLI 暫行）

- `coupons.status` 新增第 5 個終態 `voided`，僅可由 `available` 轉入（限未過期），不可逆；重複注銷、狀態不符一律拒絕並報錯
- 新增兩張表：`coupon_manual_actions`（稽核表，記錄操作者 `admin_user_id`、必填 reason、選填 ticket_reference）、`coupon_event_log`（比照 `member_event_logs` 精神新建的 coupon 層級事件表）
- 現階段無後台 CRUD API，由 RD 依規格以 CLI 執行（`coupon_id` + `member_id` 交叉確認 + 單一 DB transaction），僅支援單筆；`voided` 完全不對前台 `get_coupons`/`get_coupon_wallet` 顯示，僅 `get_coupon_detail` 直接查詢時誠實回傳
- 完整資料流規格見新文件 `docs/misc/2026-07-23-coupon-manual-void-mechanism.md`；已同步更新 CLAUDE.md（Coupon 狀態 enum）、PRD（§二 Coupon 規則、§三 狀態機）、`get_coupon_detail.md`（`status` 可回傳值）

## 2026-07-23 — get_member_orders：coupon_usage_summary 改為依 campaign_id 分組，新舊券合併呈現

- 分組鍵由 `campaign_name` + `is_new_issued` 改為 `campaign_id`（新增此欄位）；同一 campaign 若同時有新券與舊券使用，合併為一筆，透過巢狀 `coupon_usage.new_issued` / `coupon_usage.existing` 分別呈現各自的 `quantity`、`total_discount_amount`（原 `discount_amount` 更名）、`used_points`（點數消耗下放至各類別）
- 訂單層級 `point_used` 明訂為各 campaign `coupon_usage.new_issued.used_points` 的加總，屬衍生欄位，非獨立來源
- 已同步更新 `get_member_orders.md`（Sample、Response items、邏輯說明）、`create_order.md`（「`get_member_orders` 用券摘要快照」段落）；PRD 未描述此 API 的 response 欄位細節，無需修改

## 2026-07-23 — get_coupons status 查詢參數改回單選，enum 納入 unsettled

- `status` 查詢參數由可複選 `status[]` 改回單選 `status`，enum 改為 `unsettled`／`available`／`consumed`／`settled`／`expired` 五選一
- `unsettled` 為 API 查詢層級的別名，等同同時查詢 `available` + `consumed`；非 coupon 狀態機（`available`/`consumed`/`settled`/`expired`）的一員，不會出現在 response 的 `status` 欄位
- 已同步更新 `get_coupons.md`（Request Parameters、使用情境、邏輯說明）、PRD（Flow 6）

## 2026-07-23 — get_coupon_wallet 欄位更名：available_coupon_count → unsettled_coupon_count

- 欄位名稱與 `available` 狀態值容易混淆（該欄位實際聚合 `available` + `consumed` 兩種狀態，並非只計 `available`），更名為 `unsettled_coupon_count`，語意改為「尚未走完流程（尚未進入 `settled`/`expired` 終態）的券」
- 已同步更新 `get_coupon_wallet.md`（Response sample、Response items、邏輯說明）、PRD（§二 Coupon Wallet 規則、Flow 6）

## 2026-07-22 — get_coupon_wallet/get_coupons 效能討論最終定案

- `get_coupon_wallet`：移除 366 天時間限制，品牌清單改為顯示所有曾操作過的品牌（不限時間）；`available_coupon_count` 聚合口徑擴大為 `available` + `consumed`
- `get_coupons`：**不採用**先前 SA 建議的「三態收斂（`available`/`used`/`expired`，禁止自由組合）」方案，維持原始四態（`available`/`consumed`/`settled`/`expired`）與可複選 `status[]`；前端改為三個獨立列表呈現——待折抵（`available`+`consumed`）、已折抵（`settled`）、已過期（`expired`），因排序鍵不同的兩個狀態（`settled`/`expired`）現在分開查詢，不需要額外統一排序鍵即可解決原本的效能疑慮
- `get_coupons` 維持不限時間，取消原本 CR 規劃的「僅顯示近一年」免責文字，避免與 `get_coupon_wallet` 顯示所有品牌的邏輯互相矛盾
- 已同步更新 `get_coupon_wallet.md`、`get_coupons.md`、PRD（§二 Coupon Wallet 規則、Flow 6）、`docs/misc/2026-07-17-...效能討論.md`、`docs/misc/2026-07-20-...perf-adjustment-plan.md`

## 2026-07-22 — create_order 銀行↔神坊連線層 timeout 定案：改為非同步 bank_get_order 查詢

- 取代先前待與銀行/SA 確認的兩個前提問題（同 `order_id` 重送機制、bank_get_order 比對後的取消流程），改以「銀行端非同步透過 `bank_get_order` 查詢該筆訂單實際結果，據以更新銀行內部折抵資料」為主要做法，不採用同 `order_id` 重送
- 若查詢結果顯示該筆折抵不應存在（例如銀行端已判定該筆刷卡應取消），仍可透過既有 `batch_finalize_orders`（action=`cancel`）取消／回沖已入帳的折抵
- 已同步更新 PRD §12.3（六角色表格）、`docs/misc/2026-07-16-timeout-待確認事項.md`（第 1 項改為請銀行確認此設計的可行性，而非開放式問題）

## 2026-07-22 — deactivate_member 改為本地寫入成功即完成，與 activate_member 不再對稱

- 決議：`deactivate_member` 只要樹配券平台本身成功寫入本地狀態（`members.is_activated = FALSE` + `member_event_logs`）即回覆成功，不需等待點數系統（`member_unauthorize`）成功；點數系統呼叫改為 best-effort，失敗時觸發告警通知工程團隊另行補正，不影響本次 API 回應
- 移除 `TREELIFE_ERROR` 錯誤碼（不再是 `deactivate_member` 的失敗情境）
- **此調整僅適用 `deactivate_member`**；`activate_member` 維持原設計（點數系統成功才寫入本地），兩者風險方向不同（deactivate 就算點數系統端未同步，本地已擋下新交易，較安全；activate 若點數系統端授權失敗但本地已開通，之後 `create_order` 扣點可能失敗）
- 已同步更新 `deactivate_member.md`、PRD §12.5（拆分為 activate/deactivate 兩個獨立六角色表格）、`docs/misc/2026-07-16-timeout-待確認事項.md`

## 2026-07-21 — get_member_orders 效能討論定案：coupon_usage_summary 改為建單快照

- 取代先前討論的「拆成兩支 API」與「攤平成逐張明細交前端彙總」兩個選項，改為：`create_order` 建單完成當下就計算好 `coupon_usage_summary`（依 `campaign_name` + `is_new_issued` 分組）與 `point_used`，寫入該筆 order 記錄
- `get_member_orders` 直接讀取快照回傳，不再於查詢當下即時 JOIN／GROUP BY，同時解決「列表查詢即時聚合成本」與「單筆訂單用券量大時 response 過大」兩個顧慮；response 結構本身不變
- 已同步更新 `create_order.md`（新增「`get_member_orders` 用券摘要快照」段落）、`get_member_orders.md`、`docs/misc/2026-07-20-coupon-perf-adjustment-plan.md`

## 2026-07-21 — batch_finalize_orders 改回 multipart/form-data + ndjson，移除筆數上限

- 與銀行端溝通後確認：銀行端可在記憶體中逐行組出 JSON Lines（ndjson），不需落地實體檔案，因此同意將 Request 格式由 2026-06-24 定案的 JSON POST 改回 `multipart/form-data`——但這次資料內容改用 ndjson，而非 2026-06-16 曾採用、後於 2026-06-24 移除的 CSV 上傳設計
- 移除單批 1000 筆上限，改以**檔案大小 < 10MB** 作為批次基準，`request_id` 對應同一份檔案固定不變，不再需要 500–1000 筆手動切批
- API 同步驗證範圍限縮為三項：`request_id` 冪等驗證、file size 檢查、file 內容可解析性檢查（`FILE_SIZE_EXCEEDED`、`FILE_PARSE_ERROR`）；原本同步階段擋下整批的 `INVALID_ACTION`（`action` 值不合法）改列為非同步 item-level 錯誤，與 `ORDER_NOT_FOUND`、`ORDER_ALREADY_FINALIZED` 同層級處理
- 已同步更新 `batch_finalize_orders.md`、PRD §6.2
- Response 維持 `200 OK`（無 body）不變，語意上代表「已受理」，實際結果仍需透過 `get_finalize_batch_status` 查詢

## 2026-07-21 — coupon 狀態 enum 統一改為小寫（修正前次誤植）

- 前次（本日稍早）針對 `get_coupon_detail` 的釐清誤把方向定為「DB 小寫、API 層轉大寫回傳」；RD 進一步確認後改為：**API 直接回傳與 DB 一致的小寫值，不做大小寫轉換**
- 影響範圍：CLAUDE.md（權威 enum 定義）、`get_coupon_detail.md`、`get_coupons.md`、`get_coupon_wallet.md`、`deactivate_member.md`、`update_member_auto_redeem_settings.md`、PRD（§二 Coupon 規則／Point Balance 規則／Flow 2／Flow 6）
- 這次調整也順便修正了 PRD 內部原有的不一致：§三 Coupon 狀態機表格本來就是小寫，但 §二 用的是大寫，兩處對不上；統一為小寫後此矛盾一併消除
- 錯誤碼（如 `NO_AVAILABLE_COUPON_AND_POINT`、`TREELIFE_ERROR` 等）不在此次調整範圍內，維持既有 SCREAMING_SNAKE_CASE 慣例

## 2026-07-21 — get_coupon_detail 三點釐清（RD 提問）

- `max_redemptions_per_order` 補註：無快照，即時讀取 campaign 當下設定值，與 `redeem_points`/`tree_points`/`cub_points` 等快照欄位不同
- `status` 補註：DB 欄位為小寫 enum，API 層一律轉大寫回傳；同步補充到 CLAUDE.md 的 Coupon 狀態 enum 定義
- 補上已過期但 DB 狀態未回壓時的顯示邏輯：系統無主動掃描機制批次更新過期券狀態，`status` 顯示須即時比對 `expired_at` 與當下時間，已過期者一律顯示 `EXPIRED`，與 `create_order` 既有券段查詢邏輯（`status = available` 且未過期為兩個獨立條件）保持一致；此原則同步寫入 CLAUDE.md 供全系統其他 API 參照

## 2026-07-17 — activate_member/deactivate_member 補充失敗情境分類

- 討論定論：API 上分兩種情境——(1) 點數系統失敗（含 timeout）：樹配券整筆失敗、狀態不變，此操作具冪等性，可安全重試；(2) 點數系統成功、樹配券本地端寫入失敗：屬非預期錯誤，回 5xx 並觸發 Sentry alert，走人工介入排查
- 已同步更新 `activate_member.md`、`deactivate_member.md`、PRD §12.5、`docs/misc/2026-07-16-timeout-待確認事項.md`（供前端參考最新結論）

## 2026-07-17 — 補充 max_selectable_auto_brand_count 僅服務 auto 的說明

- RD 提問：DB 欄位是否可對齊 `max_selectable_auto_brand_count`、此值是否確定僅給 auto 使用
- 確認：此命名已於 2026-07-02 定案（原名 `max_selectable_brand_count`），DB 欄位對齊屬追上既有 spec，非新決策；業務規則上此欄位現階段確實僅服務 `auto` campaign，`manual` 品牌選擇機制目前無對應執行流程
- 於 `get_current_rotation.md` 邏輯說明與 PRD §4.4 補充：`manual` 品牌若未來需納入選擇上限，須重新設計（可能修改或新增 DB 欄位），非本欄位現有語意涵蓋範圍

## 2026-07-16 — PRD 新增第十二章「網路層 Timeout 因應原則」

- 盤點系統中所有同步跨系統呼叫（create_order↔treelife、create_order 銀行↔神坊、batch_finalize_orders ack、activate_member/deactivate_member↔treelife、update_member_selected_brands）可能因網路層因素 timeout 的情境
- 以「券、點、銀行、前端、營運、客服」六角色格式統一呈現因應做法：
  - create_order→treelife 扣點逾時：既有機制（cronjob 對帳），內容自 §5.3 搬移過來改寫，銀行與客服皆定案為不需得知中間狀態
  - batch_finalize_orders 等待 ack 逾時：定案為冪等重送，`BATCH_REQUEST_ALREADY_EXISTS` 視為受理確認
  - activate_member/deactivate_member→treelife 逾時：定案為直接重試（授權/解除操作本身冪等），不需對帳機制
  - update_member_selected_brands 逾時重送：建議前端先查證（重新呼叫 `get_member_settings`）再決定是否重送，避免誤判「每 N 天一次」額度已用
  - create_order 銀行↔神坊連線層 timeout：待與銀行/SA 確認技術能力後定案，PRD 先留待確認段落
- §5.3「點數端失敗」段落改為指向新章節的指路句

## 2026-07-16 — create_order response 新增 created_at

- 新增 `created_at`：order 於神坊資料庫中的建立時間（stage 1 建單當下），供發卡主機做對帳參考
- 與 request 帶入的 `transaction_time`（刷卡交易時間）為不同欄位，互不影響

## 2026-07-16 — 簡化扣點逾時處理：移除重複的同步階段查詢

- 發現同步階段與每日 cronjob 階段對「確認成功」的處理動作完全相同（皆為呼叫返點退點），沒有理由查兩次
- 簡化為：同步階段 timeout 後不查詢，直接標記「點數結果未定」交每日 04:00 cronjob 統一查詢與退點；未來優化方向（待點數系統支援拆分查詢）則改為同步階段就地查詢並續行發券，不再需要 cronjob
- 已同步修正 `create_order.md`、`CLAUDE.md`、PRD §5.3

## 2026-07-14 — 修正前次誤植：扣點逾時處理的「用點結果確認」機制其實仍有效

前次（本日稍早）改動誤將「用點結果確認」整段查詢機制視為不可用，實際限制範圍較窄：

- **實際限制**：確認扣點**成功／失敗／timeout** 的查詢本身仍可正常運作；限制僅在於「確認成功」時，點數系統**目前無法同時提供** `tree_points`/`cub_points` 細部拆分，缺此資料無法正確發券記帳
- **目前處理**：同步階段（15 秒內）查詢確認成功 → 因缺拆分資料，呼叫**返點**（`return_point`）退點，本次新券段視為失敗；確認失敗 → 走一般失敗路徑；仍未定 → 交每日 **04:00** cronjob 對帳（機制維持現行有效，非未來功能）
- **未來優化方向**：待點數系統支援同步回傳拆分後，確認成功分支改回續行發券並回寫 `tree_points`/`cub_points`，不再需要退點
- 已同步修正 `create_order.md`（含步驟 8 的交叉引用、失敗類型彙整表）、`CLAUDE.md`、PRD §5.3

## 2026-07-14 — 修正扣點逾時處理與實際能力不符（create_order／CLAUDE.md／PRD）

- 點數系統**目前**無法查詢扣點結果、也無法查詢 tree_points/cub_points 細部拆分，先前文件描述的「同步階段 timeout 後查詢確認、仍未定則交每日 cronjob 對帳」機制無法實作
- **目前實作**：timeout 後直接呼叫點數系統退點，將本次點數視為已扣除並全數退還會員（不論實際是否扣點成功），新券段本次視為失敗（不發新券）
- 原設計（用點結果確認＋cronjob 對帳）保留於文件中，改列為**未來優化方向**，待點數系統支援結果查詢後啟用

## 2026-07-14 — create_order response 欄位 summary 更名為 coupon_summary

- 語意不變，僅更名：`summary` → `coupon_summary`（含 `new_issued`/`existing` 兩組彙總結構）
- 同步更新 `create_order.md` 與 PRD §5.2/§5.4/Flow 7a 對應段落

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
