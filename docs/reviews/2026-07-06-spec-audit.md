# Spec Audit 全專案復盤報告 — 2026-07-06

> 本報告只列問題，**不做業務決定**。每條 issue 的解讀選項須由使用者裁決後，才由 `doc-update` 修改對應 spec，並同步更新 CLAUDE.md（若涉及權威業務規則）與 CHANGELOG。

## 統計摘要

| 項目 | 數值 |
|---|---|
| 審查文件數 | 16 份現役 API spec（`docs/api/**`） |
| 排除文件 | `update_member_settings.md`、`finalize_order.md`（已棄用） |
| 原始 issue 數 | 142（Phase 2 逐份 130 ＋ Phase 3 跨文件 12） |
| 去重後 issue 數 | 88（跨文件合併 17 ＋ 檔案專屬 71；合併消去 54 條重複） |
| Severity 分布 | High 24 ／ Medium 41 ／ Low 23 |

**issue 最多的前三份文件（去重前）**：
1. `create_order.md` — 11
2. `batch_finalize_orders.md` — 9
3. `activate_member.md` / `deactivate_member.md` / `get_coupon_wallet.md` / `get_current_rotation.md` / `get_finalize_batch_status.md` 並列 — 各 9 / 8

**健康項（查證後跨檔一致，記錄以免誤判）**：Coupon 狀態 enum（`AVAILABLE`/`CONSUMED`/`SETTLED`/`EXPIRED`）跨全檔一致；`MEMBER_NOT_ACTIVATED` 會員啟用檢查一致，且 `get_order` 正確採例外回 `ORDER_NOT_FOUND`。

---

## Part 1 — 跨文件合併議題（AUD-001 ～ AUD-017）

### AUD-001 · High · API Key / IP 白名單失敗全域無錯誤碼
- **涉及**：幾乎全部 12 份前台 `/coupon` spec 及 4 份 `/bank` spec 的權限需求段（P3-K，合併 14+ 條逐檔回報）
- **current_spec**：各 spec 權限需求段均列「API Key 須為專屬授權」「來源 IP 須在白名單內」兩項邊界檢查，但全 `docs/api` 無任何 401/403 或 `INVALID_API_KEY`/`IP_NOT_ALLOWED`/`UNAUTHORIZED` 定義（Grep 命中 0）。
- **ambiguity**：認證/IP 失敗回什麼？A. 由 Gateway/中介層統一處理，應在 CLAUDE.md 或 docs 索引集中定義一次共用權限錯誤碼；B. 各 spec 各自補 401/403（涉全 16 份批量修訂）。

### AUD-002 · High · log 表名分歧 member_event_logs vs member_activation_logs
- **涉及**：activate_member、deactivate_member、update_member_selected_brands、update_member_auto_redeem_settings、CLAUDE.md（P3-A）
- **current_spec**：四份 spec 正文皆寫入 `member_event_logs`；CLAUDE.md 權威為 `member_activation_logs`（action=ACTIVATE/DEACTIVATE）＋ lazy cleanup 的 `system_clear_brands`。deactivate changelog 自稱已改 `member_activation_logs` 但正文仍寫 `member_event_logs`。activate 內部 type 值亦自相矛盾（`active_member` vs `activate_member`）。
- **ambiguity**：A. `member_event_logs` 為統一事件表，CLAUDE.md 過時 → 修 CLAUDE.md 並統一 type；B. CLAUDE.md 權威，四份 spec 正文與 changelog 均錯 → 修 4 份 spec。另需釐清 `get_member_settings_change_logs` 資料來源是否即此表（其 type enum 未含 activate/deactivate，恐涵蓋缺口）。

### AUD-003 · High · max_redemptions_per_order「0」語意衝突
- **涉及**：get_current_rotation、create_order、get_coupon_detail、get_coupons（P3-D + 逐檔）
- **current_spec**：get_current_rotation 明載「0＝無上限」；create_order 清算式 `remaining_per_order_quota = max_redemptions_per_order - active_campaign_coupon_used_count`，<=0 即跳過發券——會把 0 當「0 張上限」。get_coupon_detail/get_coupons 未載「0＝無上限」。
- **ambiguity**：展示端（0＝無上限）與清算端（0＝不可發券）解讀相反，屬實質邏輯衝突；需釐清清算端是否對 max=0 特判無上限。get_coupon_detail/get_coupons 應補齊「0」語意。per-campaign vs per-order 語意跨檔一致（皆 per active campaign per order）。

### AUD-004 · High · create_order 中間表名 rotation_campaigns 應為 brand_rotation_campaigns
- **涉及**：create_order（L88）、get_current_rotation、CLAUDE.md（P3-E）
- **current_spec**：create_order 寫 `rotation_campaigns`；其餘全系統與 CLAUDE.md 為 `brand_rotation_campaigns`（2026-07-02 定名）。
- **ambiguity**：單一解讀——未同步 rename 的殘留，應改為 `brand_rotation_campaigns`（仍請確認後由 doc-update 執行）。

### AUD-005 · High · create_order rotation 結束欄位名 end_at 應為 end_time
- **涉及**：create_order（L116）、get_current_rotation、get_member_settings_change_logs、CLAUDE.md（P3-F）
- **current_spec**：create_order 用 `rotation.end_at`；其餘全系統與 CLAUDE.md 用 `end_time`。
- **ambiguity**：單一解讀——過時欄位名，應統一 `end_time`。附記 create_order「rotation 邊界暫定、以收到 request 時間為準」屬清算基準，與 active 判定的「含邊界」屬不同層面，建議交叉標註。

### AUD-006 · High · 棄用名詞 member_unauthorize 復活
- **涉及**：deactivate_member（正文/changelog）、activate_member、CLAUDE.md（P3-B）
- **current_spec**：deactivate_member 於 2026-07-05 以 `member_unauthorize` 作為 Treelife 下游 API 名重新引入；CLAUDE.md 將 `member_authorize`/`member_unauthorize` 標「文件中不得再新增使用」。activate 對下游未具名。
- **ambiguity**：A. 棄用僅限本系統對外命名，下游確有此 API → CLAUDE.md 需補註範圍；B. 棄用為全文件範圍 → 需改中性描述。兩份對下游命名處理不對稱（一具名一不具名）。

### AUD-007 · Medium · discount_rate 除零與捨入規則跨檔分歧
- **涉及**：get_current_rotation、get_order、get_coupons、get_coupon_detail（P3-C + 逐檔 R-04/R-02）
- **current_spec**：get_current_rotation 為 `Float | null`、redeem_points=0 回 null、明示一般四捨五入；其餘三份為 `Float`、無除零與捨入規則。
- **ambiguity**：A. coupon 快照場景 redeem_points 恆 >0，標註即可、型別維持 Float；B. 統一為 `Float | null` 並補捨入規則。

### AUD-008 · Medium · finalize_order（單數）名稱殘留
- **涉及**：get_order、get_finalize_batch_status、bank_get_order、create_order、batch_finalize_orders changelog、CLAUDE.md（P3-G）
- **current_spec**：多份現役 spec 正文以 `finalize_order` 指稱結案動作；CLAUDE.md 發卡主機清單只有 `batch_finalize_orders`/`get_finalize_batch_status`；finalize_order.md 已標 Deprecated。
- **ambiguity**：A. 敘述性泛指結案動作，用詞應更新為 `batch_finalize_orders`；B. 逐處改為批次 API 名。屬明確待修殘留。

### AUD-009 · Medium · get_coupon_wallet vs get_coupons 改名 changelog 矛盾
- **涉及**：get_coupon_wallet、get_coupons、CLAUDE.md（P3-I）
- **current_spec**：兩份 spec 現役並存、功能不同（wallet＝品牌卡片摘要／coupons＝品牌內券列表）且互相引用；但 get_coupons changelog 記載「由 get_coupon_wallet 改名而來」，暗示 wallet 已廢。
- **ambiguity**：A.（傾向）兩者並存，get_coupons changelog「改名」為誤植殘留，應修 changelog 措辭；B. wallet 應已廢（與現役、CLAUDE.md 雙列、功能不同不符）。

### AUD-010 · Medium · member_id 型別 UUID / 64 字 / 36 字不一致；order_id 字元集下游未複述
- **涉及**：多數前台 spec + activate/deactivate/get_member_orders/get_order（member_id）；create_order vs bank_get_order/get_order/batch_finalize_orders（order_id）（P3-J）
- **current_spec**：member_id 標「UUID」（8 份）、「最多 64 字」（activate/deactivate/get_member_orders）、「最多 36 字」（get_order）三種。order_id：create_order「64 字＋英數字底線＋全系統唯一」，下游三份僅「最多 64 字」。brand_id 已統一 ULID（一致）。
- **ambiguity**：member_id 應統一為「UUID（36 字）」或「最多 64 字」擇一權威型別；order_id 下游建議交叉標註來源約束避免驗證過寬。

### AUD-011 · Medium · MEMBER_NOT_FOUND vs MEMBER_NOT_FOUND_IN_TREELIFE
- **涉及**：activate_member、deactivate_member、其餘用 MEMBER_NOT_FOUND 之前台 spec（P3-L）
- **current_spec**：activate 對「member 不存在於小樹生活」用 `MEMBER_NOT_FOUND_IN_TREELIFE`；deactivate 及其餘全用 `MEMBER_NOT_FOUND`。
- **ambiguity**：A. activate 查 Treelife（新用戶首次啟用）語意確不同，兩碼並存合理但需明確觸發條件並檢視 deactivate 是否也需 IN_TREELIFE 變體；B. 統一為單碼。activate/deactivate 對「呼叫點數系統但會員不存在」處理不對稱。

### AUD-012 · Medium · 分頁 limit 無上限 / page 越界 / 非法參數無錯誤碼
- **涉及**：get_coupons、get_member_settings_change_logs、get_member_orders（R-01/R-02 群）
- **current_spec**：page/limit 僅標「>0」或「1~20」，多數未定義 limit 上限、page 超總頁數、非整數/負值/缺漏的行為；400 清單未涵蓋分頁參數違規。
- **ambiguity**：A. 違規回 400（需新增碼）；B. 靜默套預設值；C. 超頁回空陣列不報錯。需統一分頁參數契約。

### AUD-013 · Medium · 排序 tie-breaker 與 collation 未定義
- **涉及**：get_current_rotation、get_member_settings、get_coupons、get_member_settings_change_logs、get_order、get_member_orders（各 R-0x）
- **current_spec**：多份定義主排序鍵（name ASC／created_at DESC／expired_at ASC 等），但未定義同值 tie-break 次鍵，且中文/英數混合品牌名的 collation（code point／筆劃／拼音）未定義。
- **ambiguity**：影響分頁穩定性與回歸測試基準。A. 以 id（ULID 含時序）為次鍵；B. 未定義即實作自由。collation 需明訂。

### AUD-014 · Medium · 多重邊界檢查失敗的回傳優先序未定義
- **涉及**：get_member_settings、update_member_selected_brands、get_coupon_wallet、get_coupons、deactivate_member、create_order 等（各 R-0x）
- **current_spec**：各 spec 權限需求列多項邊界檢查，但未定義多項同時失敗時的回傳優先序（如 member 不存在且未啟用先回哪個）。
- **ambiguity**：A. 依列出順序短路；B. 認證類先於業務類。牽涉冪等（ORDER_ALREADY_EXISTS 是否應最先判）與資訊洩漏（能否藉錯誤碼探測 member 是否存在）。

### AUD-015 · Low · order_status enum 未登錄 CLAUDE.md 權威表
- **涉及**：get_order、get_member_orders、bank_get_order、get_finalize_batch_status、CLAUDE.md（P3-H）
- **current_spec**：`PROCESSING`/`COMPLETED`/`CANCELLED` 跨 4 份一致；CLAUDE.md 權威 enum 表僅列 coupon 狀態，未收錄 order_status。
- **ambiguity**：跨檔一致非衝突，但無單一權威來源有漂移風險。A. 補登至 CLAUDE.md；B. 維持現狀。屬治理建議。

### AUD-016 · Low · 時間欄位精度 / 時區標註不一致
- **涉及**：get_coupon_detail、get_order、get_member_orders、bank_get_order、get_finalize_batch_status（各 R-0x）
- **current_spec**：expired_at 標毫秒精度（`...59.999+08:00`），created_at/finalized_at 等未標精度、範例為秒級；部分欄位漏標 UTC+8 或偏移量字尾。
- **ambiguity**：A. 非毫秒欄位刻意秒精度；B. 未規範、實作可能回毫秒需前端容錯。屬格式嚴謹度，非邏輯衝突。

### AUD-017 · Low · brand.logo 無值時回傳未定義
- **涉及**：get_coupon_wallet、get_coupon_detail（R-09/R-07）
- **current_spec**：logo 型別 String、說明為品牌 logo URL，未標可空性。
- **ambiguity**：品牌未設定 logo 時回 null／空字串／預設 placeholder URL 未定義。

---

## Part 2 — 檔案專屬議題（AUD-018 ～ AUD-088）

### get_current_rotation.md
- **AUD-018 · Medium** — active rotation 交界重疊行為。current_spec：靠建立時 `next.start_time > prev.end_time` 保證不重疊，但後台 CRUD（第二階段）尚未上線。ambiguity：既存資料若相鄰邊界相等/重疊，本 API 在該瞬間回哪一筆？依賴上游保證 vs 本 API 需 tie-break，未定義「假設被違反」的行為。
- **AUD-019 · Low** — description JSON 異常。current_spec：`{"order_amount":N,"point_amount":N}` 由前端 parse。ambiguity：為空/格式異常/欄位缺失時回什麼（空字串/`{}`/null）未定義。
- **AUD-020 · Low** — max_selectable_auto_brand_count 邊界。current_spec：Sample 為 3。ambiguity：0 與「上限>實際符合品牌數」語意未定義；前端行為由該值或 brands 長度決定未明。
- **AUD-021 · Low** — campaigns 陣列空值斷言。current_spec：入選品牌 campaigns 回所有 active（auto+manual）。ambiguity：文字未明確斷言「campaigns 不會為空」，讀者無法確定空陣列是否合法回傳。

### create_order.md
- **AUD-022 · High** — ORDER_ALREADY_EXIST 拼字不一致。current_spec：L38/L119 為 `ORDER_ALREADY_EXIST`，L126（400 清單）為 `ORDER_ALREADY_EXISTS`（尾 S）。ambiguity：正式碼以哪個為準，實作端無法確定對外字串。
- **AUD-023 · High** — auto_redeem 檢查點缺失。current_spec：400 清單有 `AUTO_REDEEM_NOT_ENABLED_FOR_BRAND`，但邏輯說明全段未提 auto_redeem_enabled 檢查點。ambiguity：未啟用即整筆失敗（前置擋掉）vs 僅跳過新券發行、舊券仍 FIFO 清算；檢查發生在流程哪一步未定義。
- **AUD-024 · High** — min_order_amount 與 discount_amount 扣抵基準。current_spec：剩餘消費額以 `coupon_min_order_amount` 累計消耗，但實際折抵用 `coupon_discount_amount`。ambiguity：兩者不等值時，剩餘消費額扣門檻值屬刻意設計 vs 其中一處為筆誤；L93「大於」邊界含端點與否未明文。
- **AUD-025 · Medium** — DB transaction 主敘述與附註打架。current_spec：L110 稱「僅在同一 DB transaction 內完成才算成功」，L111 附註「是否同一 transaction 待討論」。ambiguity：已定案 vs open question；連帶扣點呼叫 treelife-api 失敗是否 rollback、如何回傳（400 清單無扣點失敗碼）未定義。
- **AUD-026 · Medium** — NO_AVAILABLE_COUPON_AND_POINT 觸發邊界。current_spec：「無任何 available coupon 且點數為 0（或無 active campaign 可發新券）」回此碼。ambiguity：有 available 舊券但全因門檻跳過（實際 0 張）、新券也發不出、最終 discount=0 時，回成功還是回此碼？點數為 0 的判定時點（扣點前 vs 張數算完）未定義。
- **AUD-027 · Low** — 券時間基準與 valid_days=0。current_spec：`expired_at =（issued_at UTC+8 日期 + coupon_valid_days）的 23:59:59.999`。ambiguity：`23:59:59.999` 未標時區、毫秒精度與 active 判定精度是否一致；valid_days=0（當日到期）行為未定義。
- **AUD-028 · Low** — 點數逐券分配跨券湊齊。current_spec：cub_points 優先、不足補 tree_points，used_tree+used_cub=該券 redeem_points。ambiguity：treelife-api 回傳總數 vs 逐券分配加總不一致時以何者為權威，未定義。

### update_member_selected_brands.md
- **AUD-029 · High** — brand_ids 重複值處理。current_spec：brand_ids 可為空陣列，未定義元素唯一性。ambiguity：`["A","A","B"]` 視為錯誤（無碼）/去重後檢查上限/不去重計入 quota——三者對 `BRAND_SELECTION_LIMIT_EXCEEDED` 觸發時機影響重大。
- **AUD-030 · Medium** — 數量上限邊界與 0。current_spec：「不得超過 max_selectable_auto_brand_count」。ambiguity：`>=` vs `>` 未明文（字面偏 length>max 違反）；max=0 時是否只能傳空陣列未明說。
- **AUD-031 · Medium** — lazy cleanup 與邊界檢查順序及副作用。current_spec：「呼叫時須先執行 lazy cleanup」，未定義與 6 項邊界檢查相對順序。ambiguity：若最終回 400，lazy cleanup 是否已執行並寫 system_clear_brands 事件（副作用是否發生）未定義。
- **AUD-032 · Medium** — diff 為空的 no-op。current_spec：空陣列也算一次異動寫紀錄，但未定義「新清單與現況完全相同」。ambiguity：diff 空不寫紀錄（no-op）vs 一律寫一筆。
- **AUD-033 · Low** — 多個問題 brand 的回報粒度。current_spec：BRAND_NOT_FOUND/BRAND_HAS_NO_ACTIVE_CAMPAIGN 拆兩碼。ambiguity：brand_ids 含多壞值（一個不存在、一個無 active campaign）時回哪碼、是否回報全部；MESSAGE 型錯誤僅回單一訊息。

### get_member_settings.md
- **AUD-034 · High** — NO_ACTIVE_ROTATION 與 lazy cleanup/空陣列互斥。current_spec：400 列 `NO_ACTIVE_ROTATION`；另有「無 active auto campaign 回 []」分支。ambiguity：無 active rotation 時一律回 400（不 cleanup）vs 仍回 200 走空陣列分支——若後者則此錯誤碼永不觸發。
- **AUD-035 · Medium** — auto_redeem_enabled 初始值。current_spec：PAUSE 後 false、RESUME 後 true。ambiguity：從未設定過的初始狀態回 true（預設啟用）還是 false（預設暫停）未定義。
- **AUD-036 · Low** — last_brand_selection_changed_at 措辭不一致。current_spec：L80「首次選牌或更換品牌時更新」，L87「僅在更換品牌時更新」。ambiguity：「更換」是否含首次選牌兩行矛盾；lazy cleanup 清空後是否保留舊時間戳未釐清。
- **AUD-037 · Low** — Endpoint 參數書寫瑕疵。current_spec：`/coupon/get_member_settings?member_id` 缺 `=value` 示意。ambiguity：書寫瑕疵，不影響邏輯但可能誤導串接者。

### update_member_auto_redeem_settings.md
- **AUD-038 · Medium** — 冪等與邊界檢查順序。current_spec：含「當前狀態已一致直接回 200，不重複寫紀錄」與「會員須已啟用」檢查。ambiguity：先邊界檢查後冪等（未啟用會員仍回 MEMBER_NOT_ACTIVATED）vs 先冪等短路（可能直接回 200）——對「未啟用會員送相同值」結果不同。
- **AUD-039 · Low** — member_event_logs 寫入內容未定義。current_spec：冪等分支「不重複寫紀錄」。ambiguity：log 是否記 action/新舊值/操作者/時間戳未說明；新版 payload 改 boolean 後 log 仍以 PAUSE/RESUME 或改記 boolean 未定義。（表名問題見 AUD-002）
- **AUD-040 · Low** — 暫停對非 AVAILABLE 券影響。current_spec：僅述暫停後 AVAILABLE 券保留、不觸發自動兌換。ambiguity：對 CONSUMED（進行中授權）/SETTLED/EXPIRED 或進行中交易的影響未說明。
- **AUD-041 · Low** — API 名稱單複數不一致。current_spec：標題/說明用單數 setting，endpoint/檔名用複數 settings。ambiguity：命名歧義，以 CLAUDE.md 權威應為複數。

### get_member_settings_change_logs.md
- **AUD-042 · Medium** — 「過去 1 年內」邊界。current_spec：多處「僅回傳 1 年內」。ambiguity：起算基準（now() vs 固定）、恰 1 年前含端點與否、自然日/日曆年/365 天（閏年差異）未定義。
- **AUD-043 · Medium** — before/after_brands 不變式。current_spec：before「首次選牌為 []」、after「系統清空為 []」。ambiguity：change_selected_brands 時兩者是否可同為 []/完全相同（空異動是否應產生 log）、元素是否去重/排序、是否受 max 上限約束未定義。
- **AUD-044 · Low** — 統一回應 envelope。current_spec：Sample 為裸物件（page/limit/total/items）。ambiguity：是否應有 code/message/data 包裝、與其他前台 spec 是否一致，本文件內無法判定。
- **AUD-045 · Low** — brand.name 硬刪除情境。current_spec：name 反查當下 brand_name，可能為已失效品牌。ambiguity：brand id 已硬刪除（非僅失效）時回 null／空字串／整筆剔除未定義。

### activate_member.md
- **AUD-046 · High** — DB 寫入失敗無回退/錯誤碼。current_spec：宣稱「兩邊皆成功才完成、任一失敗整筆失敗」，先呼叫點數系統成功才寫 DB；400 僅列 MEMBER_NOT_FOUND_IN_TREELIFE、TREELIFE_ERROR。ambiguity：點數成功但寫 DB 失敗分支無行為/錯誤碼；是否需補償回滾點數授權未描述。
- **AUD-047 · Medium** — reactivate 分支。current_spec：檢查存在且 is_activated=true 則回 200；否則呼叫點數系統。ambiguity：「存在但 is_activated=false（曾停用）」與「完全不存在」都落入否分支，重複啟用是否需與首次啟用不同 log/data 未定義。
- **AUD-048 · Medium** — 點數系統 timeout 歸類。current_spec：點數失敗回 TREELIFE_ERROR。ambiguity：逾時/無回應是否等同失敗回此碼，或另有重試/逾時門檻未寫。
- **AUD-049 · Medium** — member_id 輸入邊界。current_spec：string、必填、最多 64 字。ambiguity：空字串/純空白/超 64 字/非 UUID 格式的行為與錯誤碼未定義；「最多」含端點與否無對應驗證碼。
- **AUD-050 · Low** — 冪等雙邊一致性。current_spec：已啟用直接回 200 不重複寫 log。ambiguity：是否核對點數系統側狀態一致（本地已啟用但點數側實際未授權）未定義。
- **AUD-051 · Low** — 並發重複啟用。current_spec：成功後依存在與否 update/insert 再寫 log。ambiguity：同 member_id 兩請求同時抵達（皆讀到不存在/未啟用）是否產生重複 members/log；無鎖定/唯一約束說明。（type active_member vs activate_member 見 AUD-002）

### deactivate_member.md
- **AUD-052 · High** — 點數成功但本地更新失敗的補償缺口。current_spec：先呼叫點數 member_unauthorize 成功才更新 is_activated=false/寫 log。ambiguity：點數已取消授權、本地更新失敗時兩邊不一致，回 TREELIFE_ERROR（語意不符）/需補償回滾/視為原子（應明示）未定義。
- **AUD-053 · Medium** — idempotent 與 member 存在檢查順序。current_spec：先檢查「已停用」為 true 直接回 200，未先判 member 是否存在。ambiguity：member 不存在時，先 MEMBER_NOT_FOUND vs 被當「非啟用」直接回 200（掩蓋不存在）未明示。
- **AUD-054 · Medium** — TREELIFE_ERROR 應為 400 或 5xx。current_spec：點數失敗回 400 TREELIFE_ERROR。ambiguity：下游依賴故障慣例為 5xx；且 timeout/網路中斷是否等同失敗、重試策略未定義。
- **AUD-055 · Low** — member_id 輸入邊界。同 AUD-049（空/空白/超長/格式）。
- **AUD-056 · Low** — deactivate 與 create_order 併發競態。current_spec：停用後 AVAILABLE 券保留但不可用於新交易，CONSUMED order 走完原流程。ambiguity：deactivate 進行中（點數已取消、本地未更新）同時有新交易，該交易成功/失敗未定義（以本地 is_activated 為準 vs 序列化拒絕）。
- **AUD-057 · Low** — 200 OK 語意可觀測性。current_spec：無 response body，idempotent 分支不寫 log。ambiguity：呼叫端無法區分「本次實際停用」與「本已停用直接返回」；是否刻意設計未說明。

### get_coupon_wallet.md
- **AUD-058 · High** — 「當前 rotation」未定義且無 active rotation 情境。current_spec：多處以「當前 rotation」為篩選基準，全文未定義其判定，也未述無 active rotation 時行為。ambiguity：回 brands:[] / 以最近已結束 rotation 為基準 / 視為錯誤回碼，未定義；是否等同 CLAUDE.md active rotation 定義未明。
- **AUD-059 · High** — 「曾選過」語意與取消/cleanup 互動。current_spec：回「當前 rotation 曾選過的所有品牌」含 count=0 者。ambiguity：先選 A 後取消，A 是否仍出現？只看目前選取清單 / 曾被選取過 / 以是否持券為準——「曾選過」偏後者但 count 聚合又暗示與持券有關。
- **AUD-060 · Medium** — available_coupon_count 聚合範圍。current_spec：只聚合 status=AVAILABLE，以當前 rotation 為基準。ambiguity：是否受 rotation 邊界限制；跨檔期歷史 campaign 但仍 AVAILABLE 的舊券（FIFO 允許續用）計入與否，若不計則實際有可用舊券卻顯示 0 恐誤導。
- **AUD-061 · Low** — 排序欄位殘留舊名 brand_name。current_spec：「排序依 brand_name ASC」，但 response 欄位 2026-07-02 已改名 name。ambiguity：排序規則欄位名未同步（殘留舊名）。（collation 見 AUD-013）

### get_coupons.md
- **AUD-062 · Medium** — status[] 非法/重複值。current_spec：每值僅接受四狀態，不帶＝全部。ambiguity：帶不被接受值（PENDING/小寫）回 400 / 忽略該值 / 整批拒絕；重複值是否去重；帶全四值與不帶是否等價（排序/分頁計數）未定義。
- **AUD-063 · Low** — CONSUMED 券無 order 關聯。current_spec：本 API 不回 order_id。ambiguity：前端需區分「授權中但可能被取消」的券時僅憑 status 無法判斷——資訊完整度提示。

### get_coupon_detail.md
- **AUD-064 · Medium** — status 即時計算 vs DB 落地。current_spec：status enum 四值，未說明 EXPIRED 判定與 expired_at 關係。ambiguity：now() 已過 expired_at 但 DB 仍 AVAILABLE 時回 AVAILABLE（落地值）vs EXPIRED（即時計算）未定義。
- **AUD-065 · Medium** — expired_at 含端點與否。current_spec：固定到期時間（毫秒精度），未說明含/不含端點。ambiguity：expired_at 該瞬間視為 AVAILABLE（now()<=）vs EXPIRED（now()<）；與 AUD-064 相關，批次作業亦需一致邊界。
- **AUD-066 · Low** — member 層隱私策略未闡明。current_spec：coupon 不存在/不屬該 member 皆合併回 COUPON_NOT_FOUND；MEMBER_NOT_FOUND/MEMBER_NOT_ACTIVATED 可區分。ambiguity：coupon 層刻意合併、member 層刻意可區分屬有意設計（需標理由）vs member 層也應考慮是否洩漏「存在但未啟用」。（本 API 不在 get_order 例外內，與全域規則不衝突）

### get_member_orders.md
- **AUD-067 · Medium** — finalized_at 在 CANCELLED 的值。current_spec：order_status 三態，finalized_at「PROCESSING 時為 null」。ambiguity：僅定義 PROCESSING 分支，CANCELLED 時有時間值 vs 仍 null 未定義。
- **AUD-068 · Low** — 無訂單空清單。current_spec：功能為訂單摘要列表，Sample total=3 但列 2 筆（示意）。ambiguity：完全無訂單時回 200/total=0/items=[]（慣例）未明文，Sample 落差可能誤讀。
- **AUD-069 · Low** — card_last_four_digits 缺值。current_spec：「固定 4 碼數字字串」，發卡主機提供。ambiguity：未提供或非 4 碼時回什麼；型別 String（未標可空）與「固定 4 碼」在缺值情境衝突。

### get_order.md
- **AUD-070 · High** — actions 多於兩筆。current_spec：order_status 由 actions 映射（CREATED→PROCESSING 等），L146「最少一筆 CREATED，finalize 後新增第二筆」。ambiguity：actions 是否可能 >2 筆（重試/部分結案），此時「最後一筆」規則是否仍成立未明確。（此為 get_order 設計「不透露狀態」以外的獨立問題）
- **AUD-071 · Low** — coupons_used 空陣列。current_spec：discount_amount=Σ coupons_used[].discount_amount。ambiguity：陣列為空則總額 0，但 create_order 是否允許 0 券訂單、本 API 是否回傳這類訂單未說明。

### batch_finalize_orders.md
- **AUD-072 · High** — 部分失敗粒度不一致。current_spec：單筆業務錯誤（ORDER_NOT_FOUND/ORDER_ALREADY_FINALIZED）逐筆記 item error 不中斷整批；但非法 action 回 422 拒絕整批。ambiguity：兩類錯誤採不同粒度（整批 vs 逐筆），呼叫端無法預期「1000 筆中 1 筆 action 錯」的結果；非法 action 是否也應改逐筆。
- **AUD-073 · High** — CANCELLED 對非 consumed 券。current_spec：CANCELLED 將該訂單所有 consumed 券依到期轉 available/expired。ambiguity：僅定義 consumed 券；已 settled（部分請款）/available/expired 券的處理，及 COMPLETED 時訂單無 consumed 券的結果未定義。
- **AUD-074 · High** — 冪等 200 vs 400 矛盾。current_spec：L43 相同 request_id「直接回原批次接收資訊（隱含 200）」；L102 相同 request_id 回 400 BATCH_REQUEST_ALREADY_EXISTS。ambiguity：同情境文件內兩種相反回應，呼叫端無法判斷重送拿到 200 還是 400；changelog 亦未收斂。
- **AUD-075 · Medium** — 1000 筆邊界含否。current_spec：「單次上限 1000 筆，超過回 BATCH_SIZE_EXCEEDED」「最多 1000 筆」。ambiguity：1000 是否合法（>= vs >）未明文；orders 下限（0/未提供/1 筆）僅隱含，建議明列 `1 <= len <= 1000`。
- **AUD-076 · Medium** — 必填欄位缺失錯誤碼。current_spec：request-level 400 僅列 request_id 缺/orders 缺空/重複/size 超限/action 非法。ambiguity：orders 內某筆缺 order_id、request_id/order_id 超 64 字、orders 內 order_id 重複、認證失敗均無對應碼。
- **AUD-077 · Medium** — 冪等/建立記錄的併發競態。current_spec：收到即建 requests+items（PENDING）立即回 200，非同步 worker 處理。ambiguity：同 request_id 兩請求近乎同時到達時建立與冪等檢查是否原子；同 order_id 在同批出現兩次、或跨批同時被 COMPLETED 與 CANCELLED 的 worker 順序與終態未定義。
- **AUD-078 · Medium** — item 狀態機未定義。current_spec：單筆失敗記 item error_code，item 初始 PENDING。ambiguity：PENDING 之後終態值（DONE/FAILED/SUCCEEDED）未列舉、成功時 error_code 值未定；非業務失敗（外部逾時/DB 異常）落入何狀態、是否重試未定義。
- **AUD-079 · Low** — ORDER_ALREADY_FINALIZED 觸發條件。current_spec：action 僅 COMPLETED|CANCELLED。ambiguity：COMPLETED 是否要求訂單當前為 consumed；對已 CANCELLED 訂單再送 COMPLETED 是否回此碼；哪些終態算 finalized 無定義。
- **AUD-080 · Low** — 200 無 body 的部分成功不可觀測。current_spec：200 OK 無 body（changelog 移除 accepted_count 等）。ambiguity：無 body 下無法從同步回應得知哪筆被接收；部分成功（vs 整批 422）僅靠 HTTP status 區分，需另查 get_finalize_batch_status。

### get_finalize_batch_status.md
- **AUD-081 · High** — status 與 completed_at 綁定。current_spec：Enum PENDING/PROCESSING/COMPLETED；completed_at「尚未完成時為 null」。ambiguity：status=COMPLETED 時 completed_at 必非 null（強綁定）vs 各自獨立可能出現中間態未定義。
- **AUD-082 · High** — 計數不變式。current_spec：total/pending/success/failed_count 四計數。ambiguity：是否恆有 pending+success+failed==total；PENDING 下各計數值；COMPLETED 下 pending 是否必為 0——不變式皆未聲明。
- **AUD-083 · Medium** — action 與 status 語意界線。current_spec：orders.action=COMPLETED|CANCELLED，另有 item status PENDING/SUCCESS/FAILED。ambiguity：action 是請求意圖還是處理結果（名稱與 status 重疊）；action=CANCELLED 且 status=SUCCESS 時是否算 finalized/寫 finalized_at 未定義。
- **AUD-084 · Medium** — item error_code 是否窮舉。current_spec：Item Error Code 表僅列 ORDER_NOT_FOUND、ORDER_ALREADY_FINALIZED。ambiguity：取消失敗/系統性失敗（逾時/內部/下游拒絕）無碼；此表是否窮舉未聲明，消費端無法據此窮舉處理。
- **AUD-085 · Medium** — 空批次/orders 陣列邊界。current_spec：total_count 為批次訂單總筆數，orders 為明細陣列。ambiguity：total_count=0 是否可能、此時 status/orders；orders 長度是否恆等於 total_count（是否分頁/上限）未定義。
- **AUD-086 · Low** — request_id 缺漏/格式錯誤與認證錯誤碼。current_spec：400 僅 BATCH_REQUEST_NOT_FOUND。ambiguity：request_id 缺/空/格式錯誤是否回此碼或另有驗證碼；API Key 失敗的 401/403 未列。

### bank_get_order.md
- **AUD-087 · Medium** — finalized_at 在 CANCELLED / discount_amount 各狀態語意。current_spec：finalized_at「PROCESSING 時為 null」，discount_amount 為「本次實際折抵總金額」Integer。ambiguity：CANCELLED 時 finalized_at 值未定義；PROCESSING（預計金額）/CANCELLED（回沖 0）下 discount_amount 語意隨狀態改變但文件未區分，銀行端可能誤讀。
- **AUD-088 · Low** — /bank IP 白名單註記。current_spec：本 /bank spec 僅列 API Key 與 order_id 存在性，未列 IP 白名單（符合 CLAUDE.md「/bank 邊界另行定義」）。ambiguity：本文件是否已是「另行定義」的完整版，或應由另一份共用文件定義並被引用——僅記錄，非缺陷。

---

## 後續處理提醒

1. 本報告只列問題、不做決定。請逐條（或分批）裁決解讀選項。
2. 定案後由 `doc-update` 修改對應 spec；若涉權威業務規則（如 AUD-002/003/004/005/006 表名與 enum），須同步更新 `CLAUDE.md` 與 `docs/changelogs/CHANGELOG.md`。
3. 建議優先處理的高風險決策點：AUD-001（全域認證錯誤碼）、AUD-002（log 表名）、AUD-003（max_redemptions=0 清算衝突）、AUD-074（批次冪等 200/400 矛盾）。
