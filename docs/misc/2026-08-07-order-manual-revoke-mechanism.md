# 訂單 Revoke 機制 — 需求討論紀錄

> **狀態：跨端定案，已據此更新 `batch_finalize_orders` / `get_order` spec（2026-08-18）。**
> 本文件為需求討論與決策紀錄；**最終實作採「`cancelled` + `cancel_reason=revoked`」而非新增 order 狀態**（見下方「最終定案」）。第二、三節之「新增 `revoked` 狀態（六態）」為討論過程之設計，已被最終定案取代，保留供脈絡參考。
> 建立日：2026-08-07 ｜ 對齊收斂：2026-08-13 ｜ 定案：2026-08-18

---

## 〇、對齊結論摘要（TL;DR）

| 項目 | 決策 |
|---|---|
| **觸發方式** | 銀行第 6 次確認失敗 → 送 `batch_finalize_orders` **獨立 `action=revoke`**（非人工 CLI），全自動 |
| **訂單狀態** | **維持五態不變**；`action=revoke` → `order.status=cancelled` + `cancel_reason=revoked`。前端零改；`get_order` 據 `cancel_reason` 對外呈現 `order_status=revoked` 供財務/銀行辨識 |
| **Coupon** | **不 void、不還點**；本單涉及之券（舊券＋新券）一律**還原成 `available`**，新券保留給用戶未來使用（方案 B） |
| **手動 void coupon** | 既有 CLI 人工注銷券機制（`docs/misc/2026-07-23-coupon-manual-void-mechanism.md`）保留，供日後如需清掉殘留券使用，但**本次 out of scope** |
| **帳務報表** | 屬帳務團隊 scope；我方僅保證 `revoked` 可被辨識（見四） |

此組合同時達成：**零 ops cost**（銀行自動觸發）＋**帳務可辨識**（`cancel_reason=revoked`，不與真退款混淆）。

> ### 最終定案（2026-08-18，取代第二、三節的「新增狀態」設計）
> - **不新增 order 狀態**：`action=revoke` 的處理**完全等同 `cancel`**（訂單→`cancelled`、`discount_amount` 歸零、`consumed` 券還原 `available`/`expired`、點不返還、`coupon_event_logs` `reverted`/`expired`），**唯一差別**為訂單記 `cancel_reason=revoked`（`action=cancel` 記 `cancel_reason=cancel`）。
> - **辨識層**：`get_order`（發卡主機端）將 `cancelled` + `cancel_reason=revoked` 對外呈現為 `order_status=revoked`；前端 `get_member_orders` 與 DB `order.status` 皆維持五態不變。
> - **已更新 spec**：`batch_finalize_orders`、`get_order`。**待辦**：`orders` 表新增 `cancel_reason` 欄位（schema）。
> - 第一節的「記帳模型／根因」與第六節「為何需要區分」之推理**仍然有效**；只是「怎麼標記」從「新增狀態」改為「`cancel_reason` 欄位 + `get_order` 衍生呈現」。

---

## 一、背景與問題

### 觸發情境
銀行呼叫 `create_order` 遇連線層 timeout（未收到回應）後，改以每 5 分鐘呼叫 `get_order`（發卡主機端）確認該筆**原始 `create_order` 的實際結果**。此確認有三種分支：

| `get_order` 確認結果 | 銀行處理 | 是否進 revoke |
|---|---|---|
| **成功** | 寫回成功資料，視為折抵成功 | 否 |
| **失敗**（明確查得該筆未成立） | 重新呼叫 `create_order` 補建 | 否 |
| **timeout**（重試至第 6 次仍無法取得確定結果） | 送 `batch_finalize_orders`（**action=`REVOKE`**） | **是（本機制）** |

僅 **timeout** 分支進入本機制；成功／失敗兩分支由銀行自行收斂。

> ⚠️ 相較前版：原設計為「轉人工 + RD CLI 手動 revoke」，對齊後改為**銀行自動送 `REVOKE` finalize action**，消除人工成本。原「銀行轉人工後不再操作」的約定，改為「第 6 次失敗自動送 `REVOKE`」，須與銀行重新約定（見待確認）。

### 帳務對不起來的根因
神坊金流報表以 `order.status` 對應銀行動作，且隱含假設「`cancelled` 一定是在沖銷一筆**真的發生過的扣款**」：`processing`→要求銀行扣款；`cancelled`→要求銀行還款。timeout 這筆訂單在我方可能已是 `processing`（產生一筆銀行實際未扣的**幽靈扣款**），若事後以 `cancelled` 收尾又產生一筆**幽靈還款**，兩者對銀行實際入帳皆「查無對應」，且與真退款無法區分（詳見附錄範例）。

**核心問題**：`cancelled` 被「真退款」與「銀行沒扣過的注銷」兩種語意共用，報表無從分辨 → 故需一個**可辨識標記**（最終以 `cancel_reason=revoked` 實作，見「最終定案」）。

### 記帳模型前提：兩條獨立結算流

神坊與銀行的結算分兩條**獨立**的流：

| 結算流 | 方向 | 週期 | 觸發時點 |
|---|---|---|---|
| **A. 折抵款** | 神坊 **付** 銀行折抵$ | 每日日結 | 該券**被折抵使用、且該筆訂單 finalized as COMPLETED** |
| **B. 信用卡點款** | 銀行 **付** 神坊 $1.087/pt | 每月月結 | 用到**小樹點(信用卡)** 兌換 |

- **純信用卡點**：100pt 換 100 元折抵券 → 月結收 108.7、日結付 100 → net 收 **8.7**（機制上日結那 100 不扣、月結那 100 不請，只留 8.7）。
- **純生活點**：100pt 換 100 元折抵券 → **無 B 流**，只剩日結付 100（折抵由神坊全額吸收）。

**核心原則（revoke / cancel 皆適用）**：銀行告知「訂單不成立」，**只代表卡交易（A 流）不成立，不代表點兌換被推翻**。點被使用換成券的行為**獨立成立**，因此：
- **B 流照常**：券已產生、點已使用，$1.087/pt 月結照收，**不受 revoke/cancel 影響**。
- **A 流遞延**：該單的 $100 折抵**不在 revoke/cancel 當下發生**；由那張**存活的券**扛著，等它**未來被折抵使用、且該次訂單 finalized as COMPLETED** 時，$100 才由銀行向神坊收取。
- 銀行**實際**扣款依此按 COMPLETED 結算，這也解釋了為何「以 `processing` 樂觀計數」的報表會對一筆永不 COMPLETED 的 revoke 單**過報**（見附錄）。

---

## 二、訂單狀態機（維持五態，不新增狀態）

> **定案**：不新增 `revoked` 狀態；`action=revoke` 落在既有 `cancelled`，以 `cancel_reason` 欄位區分。（下方保留原「六態」設計脈絡，已被取代。）

```
pending ──► processing ──► completed   (action=complete)
   │            │
   │            └──► cancelled   (action=cancel  → cancel_reason=cancel  ：真退刷)
   │                            (action=revoke  → cancel_reason=revoked ：銀行未確認撤銷)
   └──► error
```

- `action=revoke` **僅可由 `processing` 轉入**（與 complete/cancel 相同）；非 processing 沿用既有 `ORDER_*` error_type。
- `cancelled` 為終態不可逆；`cancel_reason` ∈ {`cancel`, `revoked`}。
- `get_order` 對外把 `cancelled` + `cancel_reason=revoked` 呈現為 `order_status=revoked`（衍生值，非 DB 狀態）；前端與 DB 皆維持 `cancelled`。

---

## 三、`REVOKE` action 處理定義

`REVOKE` 為 `batch_finalize_orders` 新增的第三種 action，走既有 batch 流程（含 `request_id`、逐筆結果經 `get_batch_finalize_result_file` 回傳）。我方收到某訂單的 `REVOKE` item 時：

### 1. Order
- 實際為 `processing` → `processing → cancelled`、`cancel_reason=revoked`、`discount_amount` 歸零（與 `action=cancel` 相同，僅 `cancel_reason` 值不同）。
- 非 `processing`（`pending`／`error`／`completed`／`cancelled`／不存在）→ 沿用既有 finalize error_type（`ORDER_NOT_FINALIZABLE`／`ORDER_FAILED`／`ORDER_ALREADY_FINALIZED`／`ORDER_NOT_FOUND`），不影響整批其他筆；**不新增 error_type**。
- 呈現：`get_order` 據 `cancel_reason=revoked` 回傳 `order_status=revoked`；前端 `get_member_orders`、DB `order.status` 皆為 `cancelled`。

### 2. Coupon（**一律還原，不 void、不還點**）

| 券種 | 定義 | 處理 |
|---|---|---|
| **舊券** | 更早的單 mint、本單 FIFO 撿來折抵的既有券 | `consumed → available`（還原） |
| **新券** | 本單當下 mint 的券 | `consumed → available`（還原，**保留給用戶未來使用**） |

- **兩者處理相同**（都是 `consumed → available`），故本機制**不需要**區分新券／舊券的 schema 前提。
- **不呼叫 `return_point`**：點→券的轉換**維持成立**（用戶付點換得的新券仍在、可用），因此無退點、亦無 tree/cub 拆分還原、退點失敗補償等問題。
- 券還原後若已過期（revoke 可能延遲數日），依系統既有 lazy expiry 原則自動視為 `expired`，不需特別處理。
- ⚠️ 需 RD 查證：現行 `batch_finalize_orders`（`CANCELLED`）對本單券的**實際行為**為何——若已是「還原為 `available`」，`REVOKE` 可沿用同一套券處理，僅差在最終 order 狀態（`revoked` vs `cancelled`）。

### 3. 點數
- **本機制不動點數。** 用戶已扣的點對應到仍存活的新券，帳面自洽。
- 若日後營運判斷某張殘留新券應真正清除並退點，走既有**手動 void coupon CLI**（`available → voided`）——**本次 out of scope**。

### 設計理由：為何是「券還原（方案 B）」，而非「新券 void + 退點（方案 A）」？

> 常見提問：既然這筆折抵沒成，何不把新券注銷、把點退回用戶？

對同一張新券，只有兩種**自洽**組合（不能只做一半）：

| 方案 | 券 | 退點 | 用戶最終持有 | 說明 |
|---|---|---|---|---|
| **A** | void | 退 | 點數 | 世界觀「交易不該發生、全抹除」 |
| **B（採用）** | 還原 `available` | 不退 | 一張可用的新券 | 世界觀「交易發生過、只是這次折抵取消」 |
| 混搭 1 | 還原 | 退 | 點數＋券 | ❌ 雙重補償 |
| 混搭 2 | void | 不退 | 什麼都沒有 | ❌ 用戶被扣點卻一無所獲 |

對齊選 **B**，理由：
1. **更省、更少一致性風險**：不呼叫外部 `return_point`，連帶免除 tree/cub 拆分還原、退點失敗補償、操作順序等一整組問題。
2. **額度無異常**：新券留存、點→券轉換成立，`max_points_per_member` 額度本就該被占用，**沒有「是否排除」的難題**。
3. **用戶不吃虧**：用戶付點換得的新券仍可於未來折抵使用（以「未來折抵機會」補償，而非「退點」）。
4. **殘留可補救**：若特例需真正清掉某券，另有手動 void CLI（out of scope）承接。
5. **與記帳模型一致（決定性理由）**：點兌換（B 流）獨立成立、$1.087/pt 月結照收；那筆抵銷的 $100 折抵（A 流）由存活的券**遞延承載**，待該券未來被使用且 COMPLETED 時才發生。**券正是這筆遞延義務的載體**——故「留券」是對的。反之，方案 A 退點會把**已成立的 B 流點兌換一併抹除**，與記帳模型衝突，且需重算信用卡/生活拆分才能正確退款。

（方案 A 的「回到未發生」原則已**明確不採用**；本設計採「交易發生過、僅折抵取消」的世界觀。）

---

## 四、給帳務團隊的資料契約（scope 邊界）

> 隔日金流報表的產生與沖正邏輯**屬帳務團隊 scope**。但對帳問題只有在帳務團隊能從我方資料分辨 `revoked` 時才會解，故我方須保證：

- `order.status = revoked` 與 `cancelled` **明確可分**。
- 提供沖正所需欄位：訂單編號、原 `discount_amount`、（若採用）`revoked_at`。
- **對帳意涵**（供帳務團隊參考）：`revoked` 單既不應產生真實「扣款」也不應產生真實「還款」。若其扣款已於先前報表送出，需以一筆與原扣款可配對、**不計入應付銀行淨額**的沖正線沖銷，對帳時與原訂單編號配對後標記為「銀行不涉入」自動核銷。

---

## 五、對既有 API／spec 的影響（已於 2026-08-18 更新）

- **`batch_finalize_orders`** ✅ 已更新：`action` 值擴充為 `complete`｜`cancel`｜`revoke`；`revoke` 處理等同 `cancel` + 記 `cancel_reason=revoked`；不合法 action 併入 `INVALID_PAYLOAD`；狀態機／既有 error_type 不變。
- **`get_order`（發卡主機端）** ✅ 已更新：`order_status` 新增衍生值 `revoked`（DB `cancelled` + `cancel_reason=revoked`）；`total_discount_amount`／`finalized_at` 與 `cancelled` 一致。
- **`get_member_orders`（前端）**：**零改動**，revoke 單以 `cancelled` 呈現。
- **`create_order`**：不受影響；還原的券回 `available` 可再被 FIFO 選用。
- **coupon spec／`voided` 規則**：不變（手動 void 為 out of scope）。
- **待辦**：`orders` 表新增 `cancel_reason` 欄位（`cancel`／`revoked`，非 cancelled 時 null）——schema 尚未更新。

---

## 六、決策紀錄：為何是這個組合（曾評估之替代方案）

| 曾評估方案 | 為何未採用 |
|---|---|
| **純人工 CLI revoke** | ops cost 高（每筆需營運提單 + RD 執行）。 |
| **plain `CANCELLED` + 券還原** | ops 省了，但落在 `cancelled` → 報表無法與真退款區分，帳務問題原地未解（除非帳務團隊報表有「還款須先有對應扣款」守門，且 cancel 穩定同天先於扣款報出——不可靠、跨夜即破）。 |
| **`REVOKE` action + 新券 void + 退點（方案 A）** | 帳務可解，但券軸引入 `return_point` 外部呼叫、tree/cub 拆分、額度排除（#4）等一整組複雜度，非必要。 |
| **✅ `REVOKE` action + 券還原（方案 B）〔採用〕** | 銀行自動觸發（零 ops）＋獨立 `revoked`（帳務可辨識）＋券只還原（免退點複雜度、免額度難題）。 |

---

## 七、對齊結果（2026-08-18 定案）

| 對象 | 結果 |
|---|---|
| **銀行** | ✅ 第 6 次失敗**自動送 `action=revoke`** 可行；`get_order` 回傳 `revoked` 可相容。 |
| **帳務團隊** | ✅ 有 `revoked` 辨識即可處理（辨識依據為 `cancel_reason=revoked` / `get_order` 的 `order_status=revoked`）。 |
| **RD** | ✅ 已釋疑：改採 `cancelled` + `cancel_reason`，不新增狀態、前端零改；`revoke` 複用 `cancel` 邏輯。 |
| **營運** | ✅「還券不退點」可接受；`void coupon` 視為後續新功能（out of scope）。 |
| **內部（欄位）** | `revoked_at` 不採用（`finalized_at` 已足）；改以 `cancel_reason` 區分。操作者欄位不需要（全自動）。 |
| **待辦** | `orders` 表新增 `cancel_reason` 欄位（schema）。帳務端「A 流按 COMPLETED 結算 vs 報表按 processing 計數」之落差，建議帳務團隊內部再對齊一次。 |

> 記帳前提（已澄清 2026-08-13）：revoke/cancel 只推翻卡交易（A 流），點兌換（B 流）獨立成立、$1.087/pt 月結照收；A 流折抵由存活券遞延，待該券未來被使用且 COMPLETED 才發生（見第一節記帳模型）。

---

## 附錄：帳務對不平的具體範例（以 5 元訂單為例）

假設進入 revoke 的那筆訂單折抵 5 元。

**Day 1**（尚未 revoke）
- 神坊報表：processing −100 → 應付銀行 **100**
- 銀行實際：從專戶扣 **95**（那 5 元 timeout、銀行端未成立）→ 對神坊而言**少扣 5**

**Day 4**（銀行送 `REVOKE`、訂單轉 `revoked`）

| | 若沿用 `cancelled` | 採用 `revoked`（沖正不進應付） |
|---|---|---|
| processing | −50 | −50 |
| cancelled（真還款） | +5 | +0 |
| 注銷沖正（memo，不進應付） | — | +5 |
| **應付銀行** | **45** ❌ ≠ 銀行實扣 50 | **50** ✅ = 銀行實扣 50 |

- 沿用 `cancelled`：Day1「少扣 5」、Day4「多扣 5」兩反向缺口，逐日／跨期都對不平（雖累計 145=145）。
- 採用 `revoked`：沖正線與原扣款可配對、不污染「應付銀行」，當日即對平，且自帶「哪張 revoke 單、對應哪筆扣款」可自動核銷。
