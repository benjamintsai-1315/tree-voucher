# Field Guide：各欄位說明

## 功能說明
一段話，包含三個要素：
1. **誰呼叫**（e.g., client_app、發卡主機）
2. **用什麼驗證**（e.g., API Key 搭配 X-Project-Id）
3. **做什麼、回什麼**（e.g., 取得該 merchant 底下所有 action_code 的狀態與統計）

## 權限需求
- **認證**：描述 Authorization header 的格式
- **邊界檢查**：列出所有資源歸屬驗證，例如：
  - `X-Merchant-Provider-Key` 必須為目標資源所屬的商戶
  - `X-Merchant-Provider-Key` 必須是該 Client 有授權可存取的

## Request Parameters 欄位定義

| 欄位名稱 | 說明 |
| -------- | ---- |
| 欄位 | snake_case 字串 |
| 類型 | `string` / `integer` / `boolean` / `array` / `object` |
| 必填 | 請求可否忽略該 key。`TRUE` = 不可忽略，缺少此 key 即報錯；`FALSE` = 可以不帶此 key |
| 可空 | 請求可否帶空值（null）。`TRUE` = 可傳 null；`FALSE` = 傳了不能為 null。若目標 API 無此需求（空值等同於未填），可省略此欄 |
| 預設值 | 省略 key 時系統採用的值；若無預設值則填 `❎` |
| 限制條件 | 字數上限、字元集、數值範圍、枚舉值等 |

### 必填 vs 可空 的四種組合

| 必填 | 可空 | 意義 |
| ---- | ---- | ---- |
| TRUE | FALSE | 一定要帶，且不能為 null（最嚴格） |
| TRUE | TRUE | 一定要帶，但可以傳 null |
| FALSE | FALSE | 可以不帶，但帶了就不能為 null |
| FALSE | TRUE | 可以不帶，帶了也可以傳 null（最寬鬆） |

若目標 API 的空值行為等同於未填（無區分必要），**可省略「可空」欄位**，不必強行填入。

### 常見類型對照
- `string`：文字，包含 UUID、日期字串
- `integer`：整數，不含小數點
- `boolean`：`true` / `false`
- `array<string>`：字串陣列

## Response items 欄位定義

| 欄位名稱 | 說明 |
| -------- | ---- |
| 欄位 | snake_case 字串，與 JSON Sample 完全對應 |
| 類型 | 同 Request，但多了 `String`（首字大寫慣例，表示 JSON string） |
| 說明 | 中文說明，若為列舉值需列出所有可能值（e.g., `ACTIVE \| INACTIVE`） |

### 計算欄位慣例
若欄位值可由其他欄位推導，需在「邏輯說明」中寫出公式：
```
quota_remaining = quota - total_granted_points
```

## 分頁欄位（列表型 API 必須包含）

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| page | Integer | 當前頁碼，從 1 開始 |
| limit | Integer | 每頁筆數 |
| total | Integer | 符合條件的總筆數（非總頁數） |

## 時間欄位格式
- 統一使用 UTC+8，ISO 8601 格式
- 範例：`"2025-10-01T12:00:00+08:00"`
- 欄位命名慣例：`created_at`、`updated_at`、`expired_at`、`valid_from`、`valid_until`

## 狀態欄位慣例
- 全大寫英文：`ACTIVE`、`INACTIVE`、`PENDING`、`CANCELLED`、`COMPLETED`
- 在 Response items 說明欄中列出所有可能值

## 400 錯誤碼命名規則
- 全大寫 SNAKE_CASE
- 以「情境」命名而非「技術錯誤」
- 常用後綴：
  - `_NOT_FOUND`：資源不存在
  - `_NOT_AUTHORIZED_TO_CLIENT_APP`：無授權存取
  - `INACTIVE_`：資源已停用
  - `INVALID_`：參數格式不合法
  - `_ALREADY_EXISTS`：資源重複建立
  - `_LIMIT_EXCEEDED`：超過商務規定上限
