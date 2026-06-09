---
name: tree-voucher-api-spec
description: Create or revise Tree Voucher 2.0 API specification Markdown from product requirements, business flows, field lists, or rough interface notes. Use when the user asks to write, define, design, review, normalize, or convert requirements into an API spec/API document for voucher-plus-cash flows, coupons, campaigns, brands, orders, client apps, issuer hosts, or front-end/back-end interface definitions.
---

# Tree Voucher API Spec

Use this skill to turn Tree Voucher 2.0 requirements into a clear API specification for engineering handoff.

## Load Context

Use these optional references when needed:

- Read root-level `background.md` when the request depends on Tree Voucher 2.0 domain concepts, coupon lifecycle, brand selection, card transaction flows, or voucher-plus-cash business rules.
- Read `references/field-guide.md` when deciding how to fill API spec fields, permission boundaries, request parameter columns, response item descriptions, pagination fields, timestamps, status values, or error codes.
- Read `references/api_sample.md` when the user wants the output to match the team's existing style or when an example structure is useful.

Load only the file needed for the current request.

## Workflow

1. Identify the API purpose:
   - Caller: client app, issuer host, internal service, or admin system.
   - Action: query, create, update, finalize, cancel, list, select, enable, disable, or delete.
   - Main resource: brand, campaign, coupon, order, transaction, user selection, or history.
   - Scenarios: parameter combinations or state transitions that change behavior.
   - Permission boundary: authentication, project scope, merchant scope, brand ownership, user ownership, or service authorization.
   - Error cases: missing resources, unauthorized access, inactive resources, invalid parameters, exceeded limits, duplicated state, or business rule conflicts.

2. Ask concise clarification questions before writing the spec if required information is missing and cannot be derived from the provided context. Do not silently invent permission boundaries, required parameters, response fields, or error conditions.

3. Choose HTTP semantics:

| Action | Method | Parameter Location |
| ------ | ------ | ------------------ |
| Query or list without state changes | `GET` | query string |
| Create a resource or trigger a business action | `POST` | JSON body |
| Replace a resource | `PUT` | JSON body |
| Partially update a resource or state | `PATCH` | JSON body |
| Delete or revoke a resource | `DELETE` | query string or JSON body, depending on existing API convention |

4. Use snake_case for API names, endpoint segments, request fields, and response fields. Start `api_name` with a verb, for example `get_brand_list`, `select_brands`, `create_order`, or `finalize_order`.

5. Keep response samples and `Response items` exactly aligned. Every response sample field must be documented; every documented response item must appear in at least one sample. For arrays, document the array field itself in the main table, then create a separate titled table for the item shape. For nested objects, prefer separate titled tables instead of mixing parent and child fields in one table.

6. Use UTC+8 ISO 8601 strings for time fields, for example `"2026-10-01T12:00:00+08:00"`.

7. Name status values and error codes in uppercase snake case, for example `ACTIVE`, `INACTIVE`, `ORDER_NOT_FOUND`, or `BRAND_LIMIT_EXCEEDED`.

## Output Format

Output the API spec in this Markdown structure unless the user asks for a different format:

````markdown
# API: {api_name}
## 功能說明
（一段話說明此 API 的目的，包含誰呼叫、使用什麼驗證、做什麼事、回傳什麼）

## 權限需求
- 認證：Authorization: `ApiKey {{client_app_api_key}}`
- 邊界檢查：（列出所有必須通過的授權、專案、商戶、品牌、使用者或資源歸屬驗證）

## 使用情境
（描述主要使用情境；若不同參數組合或狀態會造成不同行為，逐一列出）

# Request
HTTP method: `{GET|POST|PUT|DELETE|PATCH}`
Endpoint: `/{namespace}/{action_name}`
Content-Type: `application/json`

## Request Header（表格）
| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{client_app_api_key}} |
| X-Project-Id | {{project_id}} |
| X-Merchant-Provider-Key | {{merchant_provider_key}}（若 API 需要商戶邊界） |

## Request Parameters
（依照請求格式標註：query / json / form）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| ... | ... | TRUE/FALSE | TRUE/FALSE | ❎ 或預設值 | 字數、格式、範圍、枚舉值等 |

# Response
## Sample（JSON）
```jsonc
{
  "example_field": "example_value"
}
```

## Response items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| ... | ... | ... |

### {array_field_name}
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| ... | ... | ... |

### 邏輯說明
（補充欄位之間的計算關係、排序邏輯、狀態轉換、特殊條件等）

## 400 錯誤回傳（TYPE: MESSAGE）
1. 情境描述：`ERROR_CODE_IN_UPPER_SNAKE_CASE`
2. ...
````

## Request Parameter Rules

- `必填`: Whether the key may be omitted. `TRUE` means omitting the key is an error.
- `可空`: Whether the key may be sent as `null`. `FALSE` means `null` is invalid if the key is present.
- `預設值`: Use `❎` when there is no default. Otherwise describe the behavior when the key is omitted.
- `限制條件`: Include string length, allowed character set, numeric range, enum values, array item constraints, or cross-field rules.

If null and omitted have the same behavior, still fill `可空` as `FALSE` unless the API intentionally accepts `null`.

## Response Rules

- For list responses, include `page`, `limit`, `total`, and `items`.
- For single resource responses, return the object directly unless the existing API convention requires wrapping.
- For arrays, the main `Response items` table should only include the array field itself, for example `coupons_used | Array | ...`; the fields inside the array must be documented in a separate titled table such as `### coupons_used`.
- Document calculated fields in `邏輯說明` with formulas, for example `quota_remaining = quota - total_granted_points`.
- State sort order when response order matters.
- List all possible enum values in the field description.

## Common Tree Voucher Error Codes

Use specific business-context error codes. Prefer these patterns when applicable:

- Resource missing: `{RESOURCE}_NOT_FOUND`
- Unauthorized scope: `{RESOURCE}_NOT_AUTHORIZED_TO_CLIENT_APP`
- Inactive resource: `INACTIVE_{RESOURCE}`
- Invalid parameter: `INVALID_{FIELD_NAME}`
- Duplicate state or resource: `{RESOURCE}_ALREADY_EXISTS`
- Business limit exceeded: `{LIMIT_NAME}_LIMIT_EXCEEDED`
- Invalid lifecycle transition: `INVALID_{RESOURCE}_STATUS_TRANSITION`

## Quality Checklist

Before final output, verify:

- `api_name` starts with a verb and uses snake_case.
- Endpoint path matches the API action and namespace.
- Required headers match the permission boundaries.
- Request parameter rows are complete and unambiguous.
- Response sample fields and `Response items` match exactly.
- Time fields use UTC+8 ISO 8601 format.
- Status values and error codes use uppercase snake case.
- 文件內僅保留 `400` 錯誤段落；其他 HTTP status 的通用說明由外部文件維護。
- Any calculated fields, pagination behavior, sorting, and lifecycle transitions are explained.
