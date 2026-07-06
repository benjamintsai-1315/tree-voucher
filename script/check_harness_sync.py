#!/usr/bin/env python3
"""check_harness_sync.py — 驗證 CLAUDE.md 的 Sub-agent 一覽表與 .claude/agents/*.md frontmatter 一致。

比對三件事：
  1. 表格列出的 agent 是否都有對應定義檔
  2. 定義檔是否都有列在表格中
  3. 兩邊的 model 等級是否一致（Haiku / Sonnet / Opus）

用法：python3 scripts/check_harness_sync.py
Exit code：0 = 一致，1 = 發現不一致，2 = 檔案結構問題（找不到表格或目錄）
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

# model 字串前綴 → 等級。新增模型系列時在此擴充（例如 fable）。
MODEL_TIERS = {
    "claude-haiku": "Haiku",
    "claude-sonnet": "Sonnet",
    "claude-opus": "Opus",
    "claude-fable": "Opus",  # Fable 視同最高階層級
}


def parse_claude_md_table(text: str) -> dict[str, str]:
    """從 CLAUDE.md 抓出 Sub-agent 一覽表，回傳 {agent_name: tier}。"""
    agents: dict[str, str] = {}
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        # 表頭：| Sub-agent | 職責 | Model |
        if re.match(r"^\|\s*Sub-agent\s*\|", stripped):
            in_table = True
            continue
        if in_table:
            if not stripped.startswith("|"):
                break  # 表格結束
            if re.match(r"^\|[-\s|]+\|$", stripped):
                continue  # 分隔列 |---|---|---|
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) < 3:
                continue
            m = re.match(r"`([^`]+)`", cells[0])
            if not m:
                continue
            name = m.group(1)
            # Model 欄取第一個詞（允許附註，如 "Sonnet（xxx）"）
            tier = re.split(r"[\s（(]", cells[2])[0]
            agents[name] = tier
    return agents


def parse_agent_frontmatter(path: Path) -> tuple[str | None, str | None]:
    """讀取 agent 定義檔 frontmatter，回傳 (name, model)。"""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None
    fm = m.group(1)
    name_m = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
    model_m = re.search(r"^model:\s*(\S+)", fm, re.MULTILINE)
    return (
        name_m.group(1) if name_m else None,
        model_m.group(1) if model_m else None,
    )


def model_to_tier(model: str) -> str | None:
    for prefix, tier in MODEL_TIERS.items():
        if model.startswith(prefix):
            return tier
    return None


def main() -> int:
    if not CLAUDE_MD.exists():
        print(f"錯誤：找不到 {CLAUDE_MD}")
        return 2
    if not AGENTS_DIR.is_dir():
        print(f"錯誤：找不到 {AGENTS_DIR}")
        return 2

    table = parse_claude_md_table(CLAUDE_MD.read_text(encoding="utf-8"))
    if not table:
        print("錯誤：CLAUDE.md 中找不到 Sub-agent 一覽表（表頭需為 | Sub-agent | ... | Model |）")
        return 2

    errors: list[str] = []
    files: dict[str, str] = {}  # name → model

    for path in sorted(AGENTS_DIR.glob("*.md")):
        name, model = parse_agent_frontmatter(path)
        if not name or not model:
            errors.append(f"{path.name}：frontmatter 缺少 name 或 model 欄位")
            continue
        if name != path.stem:
            errors.append(f"{path.name}：frontmatter name「{name}」與檔名不一致")
        files[name] = model

    # 1. 表格有、檔案缺
    for name in table:
        if name not in files:
            errors.append(f"表格列出「{name}」但 .claude/agents/{name}.md 不存在")

    # 2. 檔案有、表格缺
    for name in files:
        if name not in table:
            errors.append(f"{name}.md 存在但未列入 CLAUDE.md 一覽表")

    # 3. model 等級比對
    for name, model in files.items():
        if name not in table:
            continue
        tier = model_to_tier(model)
        if tier is None:
            errors.append(f"{name}.md：無法辨識的 model「{model}」（請更新腳本 MODEL_TIERS）")
        elif tier != table[name]:
            errors.append(
                f"{name}：表格為 {table[name]}，但 frontmatter 是 {model}（{tier}）"
            )

    if errors:
        print("❌ Harness 一致性檢查失敗：")
        for e in errors:
            print(f"  - {e}")
        print(f"\n共 {len(errors)} 個問題。權威來源為 CLAUDE.md 的 Sub-agent 一覽表。")
        return 1

    print(f"✅ 一致性檢查通過：{len(table)} 個 agent，表格與 frontmatter 完全同步。")
    return 0


if __name__ == "__main__":
    sys.exit(main())