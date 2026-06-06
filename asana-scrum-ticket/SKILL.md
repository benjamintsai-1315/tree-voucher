---
name: asana-scrum-ticket
description: Create scrum tickets in Asana from product ideas, requests, bug reports, specs, or implementation needs. Use when the user wants to open an Asana task/ticket and expects the description to include Context, User Story, and To-do sections, with optional SPEC references and a concise scrum-friendly title.
---

# Asana Scrum Ticket

Use this skill when the user wants Codex to create an Asana scrum ticket with a consistent structure.

## Load Context

- Read `references/ticket-template.md` before drafting the task body.
- Read user-provided PRD, SPEC, API docs, or notes only when they are needed to understand why the work exists or what work items should be listed.

## Workflow

1. Identify the minimum ticket metadata needed for creation:
   - title
   - target project
   - optional section / assignee / due date

2. If the target Asana project is not explicitly given, use Asana search to find the most likely project. Ask a concise clarification question only if the destination is still ambiguous.

3. Draft the ticket body using the exact section order below:
   - `# Context`
   - `# User Story`
   - `# To-do`

4. Write `Context` as 2 to 5 short bullets or a short paragraph explaining:
   - current business or product background
   - why this work matters now
   - what problem, risk, or opportunity is being addressed

5. Add `User Story` only when it genuinely helps clarify user value. Use this format:
   - `我是 {角色}，我想要 {目標}，所以需要 {能力或改動}`
   If the work is purely technical and no meaningful user-facing story exists, write `不適用（純技術任務）`.

6. Write `To-do` as a flat checklist of concrete work items:
   - describe what needs to be done, not full implementation specs
   - keep each item focused and action-oriented
   - when detailed behavior belongs in another document, add a SPEC reference inline
   - preferred reference format: `（SPEC: {file_or_doc_name}）`

7. Keep the ticket concise:
   - avoid long prose
   - avoid mixing acceptance criteria, design detail, and implementation detail unless the user asked for them
   - avoid inventing requirements that are not supported by the source material

8. Before creating the task in Asana:
   - confirm the title is concise and scrum-friendly
   - confirm the body contains all three sections
   - confirm every To-do item is actionable

## Asana Tooling

- Use `search_objects` first to find the target project, section, or assignee when needed.
- Use `create_tasks` by default to create the ticket immediately.
- Use `create_task_preview_v4` only when the user explicitly asks to preview before creating.

## Output Template

Use this Markdown structure for the Asana task description:

```markdown
# Context
- ...

# User Story
我是OOO，我想要做XXX，所以需要ZZZ

# To-do
- [ ] ...
- [ ] ...（SPEC: xxx）
```

## Title Guidance

- Prefer `{動詞}{目標}` or `{模組}：{要完成的事}`
- Keep it short enough to scan in backlog views
- Avoid vague titles such as `處理問題` or `調整功能`

## Quality Checklist

Before creating the Asana task, verify:

- the project destination is correct
- the title is specific
- `Context` explains why the task exists
- `User Story` is meaningful or explicitly marked not applicable
- `To-do` is a short checklist, not a full spec
- any deeper requirement is referenced to a SPEC document instead of duplicated
