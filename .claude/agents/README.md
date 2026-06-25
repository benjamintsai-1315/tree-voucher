# .claude/agents/ — MCP 工具對應說明

## Asana MCP

| 原始名稱（files/ 範本） | 實際 MCP tool 名稱 |
|---|---|
| `mcp__asana__get_projects` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__get_projects` |
| `mcp__asana__get_tasks` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__get_tasks` |
| `mcp__asana__get_task` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__get_task` |
| `mcp__asana__create_tasks` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__create_tasks` |
| `mcp__asana__update_tasks` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__update_tasks` |
| `mcp__asana__add_comment` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__add_comment` |
| `mcp__asana__get_me` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__get_me` |
| `mcp__asana__get_users` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__get_users` |
| `mcp__asana__search_tasks` | `mcp__3f94cc02-cc0c-49aa-84f1-70366a13d5b8__search_tasks` |

## Gmail MCP

| 原始名稱（files/ 範本） | 實際 MCP tool 名稱 |
|---|---|
| `mcp__gmail__create_draft` | `mcp__4eb223a0-adfa-4563-8421-220c13841328__create_draft` |
| `mcp__gmail__search_threads` | `mcp__4eb223a0-adfa-4563-8421-220c13841328__search_threads` |

## 說明

若 MCP instance 更換（tool ID 前綴改變），只需更新：
1. 本 README.md 的對應表
2. 各 agent .md 檔案 frontmatter 的 `tools:` 欄位
