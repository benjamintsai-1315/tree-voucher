---
name: spec-audit
description: >
  對整個專案的 spec 文件執行全面性業務邏輯復盤（audit），找出未定義或有歧義之處：
  步驟/條件交互的優先順序與例外、二元判斷（成功/失敗、有效/無效）只定義部分情境、
  邊界值未定義（>= 或 >、含或不含端點）、錯誤碼涵蓋範圍與實際情境不對應、跨文件矛盾。
  輸出為標註「目前 spec 現況」vs「不清楚之處」的問題清單，絕不代替使用者做業務決定。
  只要使用者提到「復盤」「全面 review」「體檢」「盤點漏洞」「audit」「找出所有歧義」
  「檢查所有 spec」或要求對多份/全部文件做邏輯審查時，一律使用本 skill——
  即使使用者沒有明確說出 skill 或 audit 這個詞。
  單一文件的審查不需本 skill，直接 spawn spec-review agent 即可。
---

# Spec Audit — 全專案業務邏輯復盤

本 skill 編排一次涵蓋全部 spec 的邏輯審查。單份文件的審查標準定義於
`.claude/agents/spec-review.md`（本 skill 不重複定義，以該檔為準）。

## 前置確認

開始前向使用者確認一件事（只問這一件）：審查範圍是否為預設的
`docs/api/**`，或需要納入/排除特定文件。
使用者若已在指令中說明範圍，直接採用，不再詢問。

## Phase 1 — 盤點（Haiku）

spawn `docs-status` 取得文件清單與最後更新時間，據此建立審查目標清單。
排除：`docs/changelogs/**`、`docs/reviews/**`、`docs/README.md`（索引與歷史紀錄不屬審查對象）。

## Phase 2 — 逐份審查（Opus，並行）

對每份目標文件 spawn 一個 `spec-review` agent，任務描述格式：

```
審查目標：[文件路徑]
範圍：單一文件內部邏輯（跨文件矛盾將於 Phase 3 另行處理，本輪僅記錄可疑引用）
```

- 每批最多並行 3 個，全部完成後再下一批（控制成本與輸出品質）
- 收集所有 `[SPEC_REVIEW]` 輸出，暫存不轉述給使用者

## Phase 3 — 跨文件一致性（Opus，單一 agent）

spawn 一個 `spec-review`，任務描述指明跨文件模式，並附上 Phase 2 各文件回報的可疑引用清單。至少檢查以下四個已知的高風險交叉點：

1. **統一術語**：brand / campaign / coupon / rotation / brand_rotation_campaigns 在各 spec 的用法是否一致
2. **Coupon 狀態 enum**：各 spec 引用的狀態是否僅限 `AVAILABLE` / `CONSUMED` / `SETTLED` / `EXPIRED`
3. **會員啟用檢查**：各前台 API 的邊界檢查是否一致使用 `MEMBER_NOT_ACTIVATED`
4. **時間邊界**：所有涉及 rotation 起訖的描述，`end_time` 是否一致為含邊界

## Phase 4 — 彙整報告

將 Phase 2 + 3 的所有 issue 合併：

1. 去除重複（同一問題在多份文件出現時合併為一條，列出所有出現位置）
2. 重新編號：`AUD-001` 起，依 severity（high → low）排序
3. 每條 issue 保留 spec-review 的欄位結構，特別是 `current_spec`（目前 spec 現況）
   與 `ambiguity`（不清楚之處＋可能的解讀選項）兩欄，缺一即為格式錯誤
4. 報告開頭加統計摘要：審查文件數、issue 總數、severity 分布、
   涉及最多 issue 的前三份文件

## Phase 5 — 交付與後續

1. 報告呈現給使用者（對話中先給統計摘要與 high severity 條目，全文寫入檔案）
2. 報告檔寫入 `docs/reviews/YYYY-MM-DD-spec-audit.md`，
   commit：`docs(misc): spec audit YYYY-MM-DD — [issue 總數] issues found`
3. 明確告知使用者：本報告只列問題，不做決定。
   每條 issue 的解讀選項由使用者裁決後，才 spawn `doc-update` 修改對應 spec，
   並提醒同步更新 CLAUDE.md（若涉及權威業務規則）與 CHANGELOG

## 行為邊界（違反即為錯誤）

- 不對任何業務邏輯下定論，不寫「建議採用 A」這類語句；只列選項與各自影響
- 不在本 skill 流程中修改任何 spec 文件（唯一寫入是 Phase 5 的報告檔）
- 使用者若中途只想看部分結果，可提前輸出已完成部分，但須標明尚未審查的文件清單