---
name: asana-scrum-ticket
description: Create scrum tickets in Asana from product ideas, requests, bug reports, specs, or implementation needs. Use when the user wants to open an Asana task/ticket and expects the description to include Context, User Story, and To-do sections, with optional SPEC references and a concise scrum-friendly title.
---

# Asana Scrum Ticket

Use this skill when the user wants to create an Asana scrum ticket with a consistent structure.

## 職責邊界

本 Skill 只負責**內容起草與品質把關**，不直接呼叫任何 Asana MCP 工具。
實際建立 ticket 的 MCP 操作一律委派給 `asana-pm` subagent 執行。

---

## Load Context

- Read `references/ticket-template.md` before drafting the task body.
- Read user-provided PRD, SPEC, API docs, or notes only when they are needed to understand why the work exists or what work items should be listed.

## 專案脈絡

本 project 所有 ticket 掛在以下 Epic 底下：
- **Project ID**：`1210249403386665`
- **Epic Task ID**：`1215416108595901`

若使用者未指定目標位置，預設掛在此 Epic 下，section 由 `asana-pm` 依現有結構判斷。

---

## Workflow

### Step 1 — 蒐集必要資訊

確認以下最小 metadata：
- title（若使用者未給，依內容擬定）
- section / assignee / due date（若使用者有提供則帶入，否則留 TBD）

### Step 2 — 起草 ticket body

依以下順序撰寫三個區段：

**`# Context`**（2–5 條 bullet 或短段落）
- 目前業務或產品背景
- 為什麼這件事要現在做
- 正在解決的問題、風險或機會
- 若有相關文件，附上文件名稱

**`# User Story`**
- 格式：`我是 {角色}，我想要 {目標}，所以需要 {能力或改動}`
- 純技術任務寫：`不適用（純技術任務）`

**`# To-do`**（flat checklist）
- 描述要做什麼，不展開完整規格
- 每項 action-oriented
- 需要細節時用 inline reference：`（SPEC: {文件名稱}）`

### Step 3 — 品質檢查

起草完成後，在送出前確認：
- [ ] title 是否具體且適合在 backlog 掃描
- [ ] `Context` 是否讓接手者知道為什麼這張 ticket 存在
- [ ] `User Story` 是否有意義，或已明確標記「不適用」
- [ ] `To-do` 是 checklist，不是規格文件
- [ ] 細節是否已 reference 到 SPEC 而非重複寫入

### Step 4 — 呈現草稿，等待使用者確認

輸出以下格式，**不執行任何操作**，等待使用者確認：

```
📋 Ticket 草稿

**Title**：[擬定標題]
**Project**：1210249403386665（tree-voucher 2.0）
**Parent Epic**：1215416108595901
**Section**：[section 名稱 或 TBD]
**Assignee**：[人名 或 TBD]
**Due**：[日期 或 TBD]

---

# Context
[內容]

# User Story
[內容]

# To-do
[內容]

---
確認建立請回覆「確認」，或說明需要調整的地方。
```

### Step 5 — 使用者確認後，委派 asana-pm 執行

使用者確認後，將以下資訊完整傳給 `asana-pm` subagent 執行建立：
- 確認後的 title
- project ID、parent epic task ID
- section / assignee / due（若有）
- 完整的 ticket body（Context + User Story + To-do）

`asana-pm` 執行完成後，回傳 `[ASANA_CREATED]` 格式；
本 Skill 直接將該結果轉給使用者，不再修改。

---

## Title Guidance

- 偏好 `{動詞}{目標}` 或 `{模組}：{要完成的事}`
- 短到可以在 backlog view 一眼掃過
- 避免模糊標題如「處理問題」或「調整功能」
