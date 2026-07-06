---
name: doc-version-diff-sa
description: Compare an uploaded document (API spec, README, technical design doc, PRD, or similar project documentation) against the corresponding file already in the current project, produce a line-by-line diff plus a thematic summary, and add a Solution Architect (SA) perspective explaining the likely reasons behind each change. Use this whenever the user attaches or uploads a new/revised version of a project document and asks to compare it, audit it, find differences, or understand what changed relative to what's in the project — including phrasing like "幫我比對這份跟專案裡的差異", "diff this against the project doc", "版本比對", "SA角度分析一下這次改了什麼", or "看看這次改版動了哪些地方". Trigger even if the user doesn't explicitly say "diff" or name this skill — attaching a revised document plus any request to compare, review, or understand the change is enough. Do not trigger for comparing two arbitrary files unrelated to an existing project, or for generic "review this document" requests with no comparison target.
---

# Doc Version Diff + SA Review

## What this skill does

Given an uploaded document and a project, this skill:
1. Finds the corresponding file already in the project
2. Extracts comparable text from both versions
3. Produces a line-by-line diff
4. Summarizes the changes thematically
5. Adds an SA-perspective interpretation of *why* each cluster of changes likely happened
6. Asks the user whether they want to act on any of it — and stops there unless they say yes

The output is always presented in chat first. Never write a diff report file to disk unless the user explicitly asks to save/record it — they've said they'll ask separately when they want that.

## Step 1: Find the corresponding project file

The user will usually not tell you exactly which project file the upload maps to — you're expected to find it yourself.

Search the project directory for candidates using, in order of signal strength:
- Filename similarity (ignoring version suffixes like `-v2`, `_final`, dates, etc.)
- Matching title/H1 heading or `# ` line inside the document
- Overlap of distinctive terms (API route names, section headers, product/module names) between the upload and candidate files

Then act based on confidence:
- **One clear match** — proceed directly. State your assumption in one line before showing results (e.g. "比對對象:`docs/api-spec.md`"), so the user can correct you if wrong, but don't stop and wait for confirmation.
- **Multiple plausible candidates, or no confident match** — stop and list the candidates (or explain nothing matched) and ask the user to point at the right file. Don't guess when it's genuinely ambiguous; a wrong diff target wastes the user's time worse than one clarifying question would.

If the user gives multiple attachments in one request, do this matching independently for each one, and handle each as its own comparison (see Step 5 for how to present multiple).

## Step 2: Extract comparable text

Different doc types need different extraction, and getting this wrong (e.g. diffing raw docx XML) produces garbage diffs full of formatting noise. Match the type to the right approach:

- **Markdown / plain text / code files (.md, .txt, source files, README, etc.)** — read directly, no extraction needed.
- **.docx** — consult the `docx` skill's guidance for reading, and extract to plain text (paragraph text only, not raw XML) before diffing.
- **.pdf** — consult the `pdf-reading` skill to extract text content. Watch out for multi-column layouts or tables that can scramble line order; if extraction looks garbled, sanity-check a section against what you know the doc should say before trusting the diff.
- **API specs in structured formats (OpenAPI/YAML/JSON)** — diff as text, but when summarizing, group by endpoint/schema name rather than raw line numbers, since that's what will actually make sense to a reader.

Write both extracted versions to temp files before diffing (this also gives you something to inspect if the diff looks wrong).

## Step 3: Generate the line-by-line diff

Use a real diff tool rather than eyeballing it — manual comparison misses things and is slower. From bash:

```bash
diff -u old_extracted.txt new_extracted.txt
```

Present this in a fenced code block with `diff` as the language tag, so additions/removals are visually distinct. Use unified format with a few lines of context (the default 3 is normally fine) — enough for the reader to locate the change without drowning them in unchanged surrounding text.

For very long documents where the raw unified diff would be huge, it's fine to show the full diff — the user asked for line-by-line, so don't pre-filter or truncate it on their behalf. If it's long, put the summary (Step 4) *before* the raw diff so the user gets the gist immediately, then the full diff below for reference.

## Step 4: Thematic summary

After the raw diff, group the changes into a short summary that a reader could skim without reading every line. Organize by what actually changed, not by line number, e.g.:

```markdown
## 變更摘要
**新增**
- 新增 `/v2/users/{id}/preferences` endpoint,支援讀取/更新使用者偏好設定

**移除**
- 移除舊版 `/v1/auth/legacy-login` 相關說明(整段刪除)

**修改**
- 認證方式從 API Key 改為 OAuth2 Bearer Token(第 3 章)
- 錯誤碼表新增 3 個項目(429, 503, 409),既有錯誤碼描述文字微調
```

Don't just restate the diff line-by-line in prose — that's redundant with Step 3. This section should let someone understand the *shape* of the change in 10 seconds.

## Step 5: SA perspective — why did this likely change?

This is the part that turns a diff into something useful for planning. For each thematic cluster from Step 4, add your best inference as a solution architect about *why* the change was probably made. Reach for these lenses (not exhaustive, and a single change can span more than one):

- **需求變更** — functionality was added/removed because product scope changed
- **效能/擴展性考量** — restructuring toward async, pagination, caching, batching, etc.
- **安全性/合規** — auth model changes, PII handling, new validation, audit fields
- **技術債/重構** — cleanup, deprecation, consolidation with no external behavior change
- **相依套件/外部系統變動** — changes forced by an upstream API, library, or platform
- **錯誤修正** — the old version was wrong or inconsistent with actual behavior
- **文件品質** — clarification/rewording with no functional change at all
- **客戶客製化** — change driven by a specific client/partner's requirement rather than a general product decision

Hedge honestly — you're inferring intent from a diff, not reading the author's mind. Use language like "可能是為了..." or "推測與...有關" rather than stating it as fact. Where the diff itself contains a strong signal (e.g. a comment, changelog note, or commit message you can see), cite it directly instead of speculating and say so explicitly — a reason grounded in evidence from the document is worth more than a plausible guess.

If a change genuinely doesn't fit any clear rationale, say so plainly ("這項變動看不出明顯原因,可能單純是編輯風格調整") rather than forcing a category onto it — false confidence here misleads more than it helps.

## Step 6: Ask about follow-up, then stop

After presenting the diff, summary, and SA analysis, ask the user whether they want to act on any of it. Do not modify, apply, or sync anything automatically — the diff is informational until the user says otherwise.

If the user says yes, don't jump straight to editing files either. First produce a concrete, itemized list of proposed changes (one item per thematic cluster from Step 4 is usually the right granularity), and let the user confirm which ones they actually want applied before you touch any project file. Some changes in the new version might be intentional improvements the user wants ported into the project; others might be exactly what the user is trying to catch and *reject*. Don't assume "yes, adjust" means "apply everything in the new version" — confirm scope item by item.

## Handling multiple attachments

If the user uploads several documents to compare at once, run Steps 1–5 for each independently, then present them as separate sections in the same response (one diff block + summary + SA analysis per document), rather than merging them into one combined diff. Ask about follow-up once at the end, covering all of them together, unless the user's phrasing suggests they care about one more than the others.
