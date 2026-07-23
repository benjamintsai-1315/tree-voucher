# 客服/營運人工注銷 Coupon 機制（CLI 暫行）

> 背景：客服／營運團隊在特殊情況（例如發券錯誤、誤發）需要手動把一張券作廢。後台 CRUD API 屬第二階段範疇、尚未開發，本文件先定義資料流與稽核機制，短期由 RD 依此規格寫單張版 CLI 腳本執行；待後台 API 開發完成後，再把同一套資料流包裝成正式 API。

## 狀態機異動

`coupons.status` enum 新增 `voided` 為第 5 個終態，轉換路徑唯一：

```
available → voided
```

- **適用範圍**：僅 `available` 狀態的券可被注銷；`consumed`／`settled`／`expired` 一律拒絕
- **可逆性**：`voided` 為真正終態，與 `settled`／`expired` 一樣不可逆，**不提供**「撤銷注銷」機制；若客服誤注銷（非打錯 coupon_id，而是真的不該注銷），正確補救方式是重新發一張新券給會員，而不是把舊券改回 `available`

## Guard Rail（CLI 執行前必須檢查）

依序檢查，任一不通過即中止並回報明確原因：

1. **coupon 是否存在**
2. **`member_id` 交叉確認**：查出該 coupon 實際所屬的 `member_id`，與輸入值比對，不符則拒絕並報錯（避免操作者輸入錯一碼 coupon_id，注銷到別人的券）
3. **狀態檢查**：`status = 'available'` 且 `expired_at > now()`（沿用系統既有原則——已實際過期但 `status` 未回壓者，視為 `expired`，拒絕注銷）
   - 已是 `voided`：拒絕並報錯「已被注銷」，**不**靜默視為成功。這點刻意不比照 `activate_member`/`deactivate_member` 對重複呼叫的冪等成功慣例，因為重複執行本操作通常代表操作者誤植 coupon_id 或搞錯狀態，應該讓這個異常被看見

執行 UPDATE 時帶 `WHERE status = 'available'`，`affected rows = 0` 則整體回滾失敗，防止 race condition。

## 新增資料表

### `coupon_manual_actions`（稽核表）

記錄人工操作的完整脈絡，是「誰、為何」的權威稽核來源，未來後台 API 化時的主要資料來源。

| 欄位 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| id | ULID (PK) | ✅ | |
| coupon_id | ULID (FK → coupons.id) | ✅ | |
| action | Enum | ✅ | 目前僅 `void`，為未來其他人工操作類型（如「人工補發」）預留擴充空間 |
| operator | String | ✅ | `admin_user_id`，由營運團隊申請時提供；CLI 執行時人工輸入，**不驗證**其存在性——發放/登記 `admin_user_id` 屬另一權限管理流程，不在本次資料流設計範圍內 |
| reason | Text | ✅ | 注銷原因（自由文字）。`ticket_reference` 本階段選填，因此 `reason` 作為最低限度的稽核依據，必填 |
| ticket_reference | String, nullable | 選填 | 客服/營運工單編號。CLI 階段不強制；未來包裝為後台 API 時，會與 proposal/approval 機制結合，屆時可能改為必填（本次 out of scope） |
| created_at | DateTime | ✅ | 操作時間 |

### `coupon_event_log`（coupon 層級事件表）

比照 `member_event_logs`（統一會員事件表）的精神新建，本次僅寫入 `voided` 一種 `type`，為未來若有其他 coupon 生命週期事件需要統一記錄時預留同一張表。

| 欄位 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| id | ULID (PK) | ✅ | |
| coupon_id | ULID (FK → coupons.id) | ✅ | |
| type | Enum | ✅ | 本次僅新增 `voided` |
| data | JSON, nullable | | 事件快照，例如 `{"previous_status": "available", "manual_action_id": "<coupon_manual_actions.id>"}` |
| created_at | DateTime | ✅ | 事件發生時間 |

**兩表分工**：`coupon_manual_actions` 是「誰、為何」的權威稽核來源；`coupon_event_log` 是 coupon 生命週期時間軸，透過 `data.manual_action_id` 關聯回稽核表，供未來查詢「這張券的完整歷程」時使用。

## CLI 執行流程（暫行，RD 操作，僅支援單筆）

1. CS/Ops 透過既有工單管道提出注銷需求（管道本身非本次設計範圍）
2. RD 執行 CLI，帶入參數：`coupon_id`、`member_id`（交叉確認用）、`admin_user_id`（操作者）、`reason`（必填）、`ticket_reference`（選填）
3. CLI 依「Guard Rail」逐項檢查，不通過則中止並回報原因
4. 通過後，於**單一 DB transaction** 內依序執行：
   a. `UPDATE coupons SET status = 'voided' WHERE id = :coupon_id AND status = 'available'`（`affected rows = 0` 則整體回滾失敗）
   b. `INSERT INTO coupon_manual_actions (coupon_id, action='void', operator, reason, ticket_reference, created_at)`
   c. `INSERT INTO coupon_event_log (coupon_id, type='voided', data={"previous_status": "available", "manual_action_id": "<上一步產生的 id>"}, created_at)`
5. CLI 輸出成功/失敗結果，供 RD 回報 CS/Ops

**本次不支援批量**：一次僅能處理一張券。若實務上有批量需求（例如一次發錯一百張），由 RD 自行寫輸出迴圈重複呼叫單張版 CLI，不在本次規格內預先設計 batch 介面。

## 對既有 API／文件的影響

- **`create_order`**：FIFO 清算查詢固定篩選 `status = 'available'`，天然不會選到 `voided` 券，無需修改邏輯
- **`get_coupons`／`get_coupon_wallet`**：**不修改**。`voided` 不加入 `get_coupons` 的 `status` 查詢參數 enum（前台不開放查詢此內部管理狀態）；`get_coupon_wallet` 的品牌入列條件（「存在任一 coupon，不限狀態」）與 `unsettled_coupon_count`（僅計 `available`+`consumed`）本來就不受影響，不會意外納入 `voided`
- **`get_coupon_detail`**：`status` 欄位可回傳值新增 `voided`——若會員或客服直接以 id 查詢該券，仍誠實回報實際狀態，不做特殊隱藏
- **會員通知**：本次**不做**自動通知（push/email）；通知系統屬另一套基礎設施，需求量預期低，如需通知由客服自行人工聯絡會員

## 待未來後台 API 化時需重新確認的事項

- `operator`（`admin_user_id`）身份是否改由登入系統自動帶入，取代 CLI 階段的人工輸入與不驗證
- `ticket_reference` 是否改為必填，並與正式的 proposal/approval 機制結合
- 是否需要支援批量注銷介面
- 是否需要在 `get_coupons`／`get_coupon_wallet` 或後台管理介面開放查詢 `voided` 狀態的券（本次定案為前台完全不可見）
