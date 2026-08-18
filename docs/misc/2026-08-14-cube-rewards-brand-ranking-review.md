# CUBE Rewards 品牌排序需求 — 問題清單（2026-08-17 審查）

> 審查對象：`docs/misc/2026-08-14-cube-rewards-brand-ranking-requirement.md`
> 比對文件：`docs/api/API Spec - get_current_rotation.md`、`docs/樹配券2.0_PRD.md`、`docs/reviews/2026-07-06-spec-audit.md`（AUD-013、AUD-061）、`CLAUDE.md`
> 性質：僅列歧義與未定義情境，不對業務邏輯下定論；各項解讀選項待需求方／內部裁決後才回頭修改文件。

## 決策記錄（2026-08-18）

品牌排序機制底定：於既有 `brand_rotation_campaigns` 表新增 `sort_order`（Integer，NOT NULL，DEFAULT 999）與 `updated_at` 兩欄位，取代原需求的「生效期間／預約排序」設計。資料更新方式為 operation 開工單、RD 以 CLI 手動更正，不做正式後台 API。

排序邏輯：category 分組（維持現況）→ 組內依 `sort_order` 由小到大 → 數值相同時維持現行 `name` 字母序 tie-break。

| 編號 | 狀態 | 說明 |
|---|---|---|
| R-01 | ✅ 已解決 | 保留 category 分組，組內依 sort_order，不採跨品牌攤平 |
| R-02 | ✅ 已解決（不再適用） | tie-break 改回 name，不使用倍率，倍率無對應欄位的問題不再相關 |
| R-03 | ✅ 已解決 | 終極 tie-break 為 name（沿用現行邏輯，非循環定義） |
| R-04 | ✅ 已解決（不再適用） | 不使用 discount_rate 做 tie-break |
| R-05 | ✅ 已解決 | sort_order 設為必填欄位，DEFAULT 999，未設定者統一排最後 |
| R-06 | ✅ 已解決 | sort_order：Integer，NOT NULL，DEFAULT 999，數字越小越前面 |
| R-07 | ✅ 已解決（不再適用） | 不做預約排序／生效時間點機制，問題不再存在 |
| R-08 | ✅ 已解決（不再適用） | 同上，不需事件表 |
| R-09 | ✅ 已解決（不再適用） | 同上 |
| R-10 | ✅ 已解決 | 比照 coupon manual void 先例，設定端以 operation 開工單、RD CLI 執行，不做正式後台 API |
| R-11 | ⏳ 仍待確認 | category 字串異動導致排序失聯的風險依然存在（因保留 category 分組），未來若要處理需另外決議 |
| R-12 | ⏳ 仍待確認 | 本次決策僅明確涵蓋 get_current_rotation；get_coupon_wallet 排序是否比照調整未討論，暫依現況（brand_name ASC）不變，非本次範疇 |
| R-13 | ✅ 已解決（不再適用） | 不需新增事件表，僅在既有表加兩欄位 |
| R-14 | ✅ 已解決（不再適用） | sort_order 必填有 default，不存在「未設定」的異常情境，不需新增錯誤碼 |
| R-15 | ✅ 已解決（不再適用） | tie-break 不再使用倍率，此操作陷阱不存在 |

## High（結構性，建議優先請需求方澄清）

- **R-01｜Category 內排序 vs 跨 Category 扁平順序矛盾**
  需求同時說「Rank 是 Category 內設定」，但範例（第1個月 A→B→C）是不分 Category 的扁平總順序，且未交代「Category 之間」誰先誰後。與現況 get_current_rotation「先分組、組內排序」的兩層結構不吻合。

- **R-02｜「品牌倍率」對映不到單一資料欄位**
  Tie-break 用的「倍率」，系統中最接近的是 campaign 層級即時計算的 `discount_rate`，非 brand 層級欄位；一品牌可能同時掛多個 active campaign（auto + manual），取哪一個未定義。

- **R-03｜終極 tie-break 循環定義，且未解掉既有 AUD-013**
  需求說「Rank 同、倍率同 → 維持 API 回傳順序」，但 API 回傳順序正是要被決定的東西，是循環定義。既有 spec-audit AUD-013（排序 tie-breaker/collation 未定義）建議以 `id`（ULID）為終極次鍵，本需求並未採用或提及。

- **R-05｜未設定 Rank 的品牌 fallback 未定義**
  現況所有品牌都還沒有 Rank（schema 無此欄位），上線初期「大部分品牌未設 Rank」會是常態，但需求完全沒描述這種情況怎麼排。

- **R-10｜設定端與 CLAUDE.md「後台 CRUD API（第二階段）屬 Scope 外」衝突**
  需求本質是「神坊可設定」的後台功能。是否比照 coupon 人工注銷先例（`docs/misc/2026-07-23-coupon-manual-void-mechanism.md`），本次只做讀取端（get_current_rotation 排序）、設定端先用 RD CLI 暫行？此交付切法未定義。

## Medium

- **R-04**：`discount_rate` 可能為 `null`（`coupon_redeem_points=0` 時）或四捨五入前後不等，倍率 tie-break 如何處理未定義。
- **R-06**：Rank 的資料型別／值域（整數/可否為 0 或負數/大小方向）未定義。
- **R-07**：若 Rank 綁定 rotation ＋ 事件式生效時間點模型，事件 `effective_at` 落在 rotation 起訖之外（早於 start / 晚於 end / rotation 尚未 active）時的行為未定義。
- **R-08**：事件粒度未定義——每筆事件是「整份排序快照」還是「單一品牌增量」，兩者語意差異大，且同 `effective_at` 撞期時的次鍵未定義。
- **R-09**：需求以「期間」思維舉例（第1/2/3個月），初步技術方向改用「時間點事件」，兩者對「期間結束後回到預設排序」「自然月邊界對齊」「事件間空窗」的表達力落差未定義。
- **R-11**：`brand_category` 是自由字串、非獨立主表，若品牌 category 被改名/打錯字，掛在舊字串下的 Rank 是否失聯未定義。
- **R-12**：需求泛稱「API Response」未指名端點——僅 get_current_rotation 套用，或連 get_coupon_wallet（現況 `brand_name ASC`）也要一併套用未定義。
- **R-13**：新增 rank 事件表的欄位契約完全空白（時間精度/時區、`rotation_id`/`brand_id` FK、主鍵型別、是否需 operator/reason 稽核欄位）。

## Low

- **R-14**：導入 Rank 後是否需要新增錯誤碼（如「有 active rotation 但無任何 rank 事件生效」），或一律靜默 fallback，未明文。
- **R-15**：需求目的情境 2（低倍率品牌應優先顯示）與需求 4 的 tie-break（同 Rank 時倍率大者優先）存在操作陷阱——若營運誤把兩品牌設成同 Rank，效果會與情境 2 的訴求相反，建議需求方留意但非邏輯矛盾。

## 總結

15 項問題（High 5 / Medium 8 / Low 2）。三個最關鍵、建議優先請需求方澄清的結構性問題：R-01（Category 內 vs 扁平排序）、R-02（倍率無對應欄位）、R-10（設定端交付形式，涉及 Scope 邊界）。R-03 額外指出本需求未解掉既有的 AUD-013 遺留問題。內部技術方向（Rank 綁定 rotation ＋ 事件式生效時間點）本身另外引出 R-07/08/09 三項新的未定義情境，建議待 R-01/R-02 定案後再細化。
