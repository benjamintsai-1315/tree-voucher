---
name: push-and-verify-pages
description: Push the current repository to its git remote and verify the deployed online page, especially for GitHub Pages or other static documentation sites. Use when the user asks to deploy, publish, push the latest docs/site version, or confirm that the live page is updated after a repository push.
---

# Push And Verify Pages

Use this skill when the user wants one bundled workflow that sends the current repository upstream and then confirms the online page is live.

## What This Skill Covers

- inspect repo status and current branch
- decide whether the repo is ready to push
- push committed changes to the correct remote branch
- derive the likely public site URL
- verify that the live page is reachable and reflects the expected version

This skill is a good fit for GitHub Pages documentation repos, especially Jekyll-style sites. It can still be used for other static sites if the deployment URL is already known from the repo.

## Load Context

Read only what is needed:

- Read root-level `index.md` when the repo looks like a documentation site and you need clues about how the site is published.
- Read `_config.yml` when the repo looks like Jekyll or GitHub Pages and you need to confirm page structure.
- Search for `CNAME`, deployment scripts, or host-specific config only if the public URL cannot be derived from the git remote.

## Workflow

1. Inspect repo state first:
   - `git status --short`
   - `git branch --show-current`
   - `git remote -v`

2. Decide push readiness:
   - If there are no local changes and the user asked to deploy the current version, push the current branch only if needed.
   - If there are uncommitted changes, do not silently skip them. Either:
     - commit them if the user clearly wants the current working version deployed, or
     - ask a concise clarification question if committing them would be ambiguous.
   - If commit is required, summarize the files being included before committing.

3. Push upstream:
   - Prefer pushing the current branch to `origin` unless the repo conventions or the user's request say otherwise.
   - If the deployment branch is obvious, use it directly. For GitHub Pages docs repos, this is often `main`.
   - If git write operations are blocked by the sandbox, request escalation with a short approval question.

4. Derive the public URL:
   - If a `CNAME` file exists, prefer that custom domain.
   - For a GitHub remote like `https://github.com/{owner}/{repo}.git`:
     - if `repo` equals `{owner}.github.io`, the site URL is `https://{owner}.github.io/`
     - otherwise assume project pages URL `https://{owner}.github.io/{repo}/`
   - If the repo already documents a canonical site URL, prefer that documented URL.

5. Verify the live page:
   - Open the public URL with a browser-capable tool when available.
   - Confirm the page loads successfully and spot-check content that proves the latest change is live.
   - Prefer checking a page or heading that was part of the current change, rather than only checking HTTP reachability.
   - If the site is still stale, wait briefly and retry at least once before reporting failure, because static-site deployments can lag behind the git push.

6. Report outcome clearly:
   - pushed branch and remote
   - commit hash if a new commit was created
   - verified URL
   - whether the page already reflects the latest content or still appears pending

## Verification Heuristics

- For index pages, verify a recently added API link, heading, or navigation entry.
- For spec sites, verify that a newly added page is accessible from the public URL and not just present in git.
- If the deployment platform exposes a 404 or stale cache page, mention that explicitly and include what you checked.

## Guardrails

- Do not create empty commits just to force deployment unless the user explicitly asks for that behavior.
- Do not assume untracked or modified files should be deployed unless the request clearly refers to the current local version.
- Do not claim the deployment is complete from `git push` alone; the online page must be checked.
- If the site URL cannot be derived with high confidence, pause and ask for the intended public URL.

## Output Checklist

Before finishing, confirm:

- which files or commit were pushed
- which branch was pushed
- which public URL was checked
- what exact evidence shows the live page is updated
