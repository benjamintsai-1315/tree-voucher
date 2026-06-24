---
title: Database Schema
permalink: /database-schema/
---

# 樹享券 2.0 Database Schema

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-24 | `coupons` 新增 `rotation_id FK`（發券時快照，供統計用）；ERD 新增 `rotations \|\|--o\{ coupons` 關聯；`campaigns` 約束補充 `type` 不可變規則 |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled`；ERD 與 constraints 同步更新 |
| 2026-06-16 | 新增 `finalize_batch_requests` 與 `finalize_batch_items` 表，支援批次非同步 finalize_order 流程 |
| 2026-06-16 | `rotations` 的 `display_coupon_min_order_amount` / `display_coupon_redeem_points` 合併為 `description`（string，JSON 格式 `{"order_amount": N, "point_amount": N}`） |
| 2026-06-16 | campaigns / coupons 欄位改名：`unit_cash_amount` → `coupon_min_order_amount`、`unit_point_amount` → `coupon_redeem_points`、`unit_discount_amount` → `coupon_discount_amount`、`max_redeem_count` → `max_redemptions_per_order`；rotations 的 `description` 改回 `display_coupon_min_order_amount` / `display_coupon_redeem_points` |
| 2026-06-15 | `member_brand_change_logs` 改為 request 粒度（一筆一次操作）；移除 `brand_id FK`；新增 `type`、`added_brand_ids`、`removed_brand_ids`（diff 於寫入時計算） |
| 2026-06-15 | `campaigns` 新增 `type`（`auto`\|`manual`）與 `rotation_id FK`；移除 `start_at`/`end_at`（active 判斷改由 rotation 繼承）；ERD 新增 `rotations \|\|--o\{ campaigns` 關聯；約束說明更新 active 判斷規則與唯一性約束 |
| 2026-06-15 | `coupons` 移除 `issued_at`（與 `created_at` 重複）；移除 `order_coupon_items` 表（快照改於發券時存入 `coupons`）；移除獨立的 `member_auto_redeem_settings` 表（`auto_redeem_enabled` 併入 `members`）；全文 `occurred_at` 統一改為 `created_at`；約束區段 PK 命名去除 table prefix，統一使用 `id`；`rotations` 的 `display_coupon_min_order_amount` / `display_coupon_redeem_points` 恢復（原曾改為 `description`，決議改回） |

---

本文件描述樹享券 2.0 的資料模型設計，使用 Mermaid `erDiagram` 表示核心實體與關聯。

設計原則：

- `coupon_wallet` 是查詢視角，不是獨立資料表。
- campaign 的 active 狀態由其 `rotation_id` 所對應的 rotation 是否為當前 active rotation 推導，不另存布林欄位。
- 點數餘額、扣點流水屬外部點數系統，本系統不另外設計點數帳務表。
- 授權狀態以 `members` 主表欄位記錄當前狀態，完整異動歷史由 `member_authorization_logs` 保存。
- API layer 可沿用 `events`、`coupons_used` 等回傳欄位；DB layer 對應名詞統一使用 `order_logs`、`order_coupon_logs`。

## Mermaid ERD

```mermaid

erDiagram
    %% --- 會員條款相關 ---
    terms_agreements ||--o{ member_terms_agreement_logs : logs
    members ||--o{ member_terms_agreement_logs : has

    %% --- 特店相關 ---
    brands ||--o{ campaigns : has
    rotations ||--o{ campaigns : scopes
    campaigns ||--o{ coupons : issues
    members ||--o{ coupons : owns

    rotations ||--o{ rotation_brands : contains
    brands ||--o{ rotation_brands : "included_in"

    %% --- 會員與特店相關 ---
    rotations ||--o{ coupons : "issued_under"
    rotations ||--o{ member_selected_brands : scopes
    members ||--o{ member_selected_brands : selects
    brands ||--o{ member_selected_brands : selected_by

    members ||--o{ member_brand_change_logs : creates
    rotations ||--o{ member_brand_change_logs : scopes
    brands ||--o{ member_brand_change_logs : targets

    %% --- 訂單系統相關 ---
    members ||--o{ orders : places
    brands ||--o{ orders : belongs_to
    coupons ||--o{ order_coupon_logs : records
    orders o|--o{ order_coupon_logs : references

    %% --- 批次 finalize 相關 ---
    finalize_batch_requests ||--o{ finalize_batch_items : contains
    orders o|--o{ finalize_batch_items : referenced_by


    %% --------------------------------------------------
    %% 資料表定義區
    %% -------------------------------------------------
    members {
        string(36) id PK
        boolean terms_agreed "僅存目前狀態，版本與異動看 log"
        boolean auto_redeem_enabled
        datetime created_at
        datetime updated_at
    }

    terms_agreements {
        string(16) version PK
        text content
        datetime created_at
        datetime updated_at
    }

    member_terms_agreement_logs {
        string(26) id PK
        string(36) member_id FK
        string(16) terms_agreement_version FK
        string action "accepted, revoked"
        datetime created_at
    }

    brands {
        string(64) id PK
        string(32) name
        string(256) logo "URL"
        string(32) category "品牌分類：便利商店、藥妝..."
        string(50) treepoint_merchant_provider_key
        datetime created_at
        datetime updated_at
    }

    campaigns {
        string(26) id PK
        string(64) brand_id FK
        string(26) rotation_id FK
        string(16) type "auto, manual"
        string(32) name
        string(64) description "預開欄位"
        int coupon_min_order_amount
        int coupon_redeem_points
        int coupon_discount_amount
        int max_redemptions_per_order
        datetime created_at
        datetime updated_at
    }

    rotations {
        string(26) id PK
        datetime start_time
        datetime end_time
        int max_selectable_brand_count
        string description "顯示用說明參數，JSON 字串，格式固定為 {\"order_amount\": N, \"point_amount\": N}"
        datetime created_at
        datetime updated_at
    }

    rotation_brands {
        string(26) id PK
        string(26) rotation_id FK
        string(64) brand_id FK
        datetime created_at
    }

    member_selected_brands {
        string(26) id PK
        string(36) member_id FK
        string(64) brand_id FK
        string(26) rotation_id FK
        datetime created_at "即 selected_at"
        datetime updated_at
    }

    member_brand_change_logs {
        string(26) id PK
        string(36) request_id "unique per operation"
        string(36) member_id FK
        string(26) rotation_id FK
        string(32) type "initial_selection, change_brand, pause, resume, system_clear_brands"
        json added_brand_ids "change_brand 時必填，其餘為 null"
        json removed_brand_ids "change_brand 時必填，其餘為 null"
        datetime created_at
    }

    coupons {
        string(26) id PK
        string(36) member_id FK
        string(26) campaign_id FK
        string(26) rotation_id FK "snapshot at issue time, for reporting"
        string(16) type "from_campaign, from_member"
        string(16) status "available, consumed, settled, expired" "consumed=交易授權中; settled=請款完成"
        int coupon_min_order_amount "snapshot"
        int coupon_redeem_points "snapshot"
        int coupon_discount_amount "snapshot"
        datetime expired_at
        datetime created_at
        datetime updated_at
    }

    orders {
        string(64) order_id PK
        string(36) member_id FK
        string(64) brand_id FK
        int order_amount
        int discount_amount
        string card_last_four_digits
        string(16) order_status
        datetime finalized_at
        datetime created_at
        datetime updated_at
    }

    order_coupon_logs {
        string(26) id PK
        string(64) order_id FK "nullable for expired"
        string(26) coupon_id FK
        string(16) type "issued, consumed, expired, updated"
        datetime created_at
    }

    finalize_batch_requests {
        string(64) id PK "由發卡主機提供的 request_id"
        integer total_count
        string(16) status "PENDING, PROCESSING, COMPLETED"
        datetime submitted_at "批次接收時間（UTC+8）"
        datetime completed_at "全部處理完成時間（UTC+8），nullable"
        datetime created_at
        datetime updated_at
    }

    finalize_batch_items {
        string(26) id PK
        string(64) request_id FK
        string(64) order_id FK
        string(16) action "COMPLETED, CANCELLED"
        string(16) status "PENDING, SUCCESS, FAILED"
        datetime finalized_at "單筆成功時間（UTC+8），nullable"
        string error_code "nullable"
        datetime created_at
        datetime updated_at
    }
```

## 關鍵欄位與約束

### members

- 主鍵：`id`
- 作為品牌設定、券、訂單與異動紀錄的關聯主體

### brands

- 主鍵：`id`
- `treepoint_merchant_provider_key` 必填，不可為 `null`

### campaigns

- 主鍵：`id`
- 外鍵：
  - `brand_id -> brands.id`
  - `rotation_id -> rotations.id`（兩種 type 皆必填）
- `type` enum：`auto`、`manual`
  - `auto`：系統自動兌換型，依附於 rotation；刷卡時自動觸發
  - `manual`：用戶手動兌換型，同樣依附於 rotation，但兌換行為由用戶發起
- campaign 的 active 判斷改為其 `rotation_id` 對應的 rotation 是否為當前 active rotation（`start_time <= now() <= end_time`）
- `coupon_min_order_amount`、`coupon_redeem_points`、`coupon_discount_amount`、`max_redemptions_per_order` 皆應大於 0
- 同一 `brand` 同一時間只允許一個 `type = auto` 的 active campaign
- `type` 一經建立不得更改；變更 `type` 會破壞上述唯一性約束，且影響已發券的歷史語意

### member_selected_brands

- 主鍵：`id`
- 外鍵：
  - `member_id -> members.id`
  - `brand_id -> brands.id`
  - `rotation_id -> rotations.id`
- 建議唯一約束：`(member_id, brand_id)`
- `rotation_id` 於用戶選擇品牌時寫入當下 active rotation 的 id，用於 lazy cleanup 判斷是否屬於舊檔期
- 表示用戶目前保留的已選品牌集合

### member_brand_change_logs

- 主鍵：`id`
- 外鍵：`member_id -> members.id`
- 一筆紀錄 = 一次完整操作（一個 `request_id`），不再以個別品牌事件展開
- `type` enum：
  - `initial_selection`：首次選牌
  - `change_brand`：品牌更換；`added_brand_ids` / `removed_brand_ids` 於寫入時預先計算並存入
  - `pause`：暫停自動兌換服務
  - `resume`：重啟自動兌換服務
  - `system_clear_brands`：系統 lazy cleanup 清空舊檔期選擇；`created_at` 設為舊 rotation 的 `end_time`
- `added_brand_ids` / `removed_brand_ids`：僅 `change_brand` 時必填，其餘為 null

### coupons

- 主鍵：`id`
- 外鍵：
  - `member_id -> members.id`
  - `campaign_id -> campaigns.id`
  - `rotation_id -> rotations.id`（發券時寫入當下 active rotation 的 id，唯讀快照，供跨檔期統計使用）
- `status` enum：
  - `AVAILABLE`
  - `CONSUMED`（交易授權中，等待商戶請款）
  - `SETTLED`（請款完成，神坊代償完畢）
  - `EXPIRED`
- `expired_at` 於發券時計算後寫死：
  - `expired_at = (created_at 所在 UTC+8 日期 + coupon_valid_days) 的 23:59:59.999`

### orders

- 主鍵：`order_id`（由發卡主機提供，本系統內唯一）
- 外鍵：
  - `member_id -> members.id`
  - `brand_id -> brands.id`
- `order_status` enum：
  - `PROCESSING`
  - `COMPLETED`
  - `CANCELLED`
- `card_last_four_digits` 僅供前台顯示，不參與清算

### order_logs

- 主鍵：`id`
- 外鍵：`order_id -> orders.order_id`
- `action` enum：
  - `CREATED`
  - `COMPLETED`
  - `CANCELLED`
- 一筆成功 `create_order` 至少建立一筆 `CREATED`
- 成功 `finalize_order` 後再新增一筆 `COMPLETED` 或 `CANCELLED`

### rotations

- 主鍵：`id`
- `start_time` / `end_time` 均為 UTC+8 時間戳記
- active rotation 以 `start_time <= now() <= end_time` 判斷
- 系統同一時間只應有一個 active rotation
- `max_selectable_brand_count`：此檔期用戶最多可選品牌數，取代原 `system_configs.brand_selection_limit`
- `description`：前端顯示用說明參數，固定以 JSON 字串寫入，格式為 `{"order_amount": N, "point_amount": N}`，由後台維護，前端自行 parse 組合說明文字，不參與任何清算邏輯

### system_configs

- 主鍵：`config_key`
- 至少應包含：
  - `coupon_valid_days`

### finalize_batch_requests

- 主鍵：`id`（即發卡主機提供的 `request_id`，最多 64 字）
- `status` enum：
  - `PENDING`：批次建立，尚未處理任何 item
  - `PROCESSING`：至少一筆 item 已處理
  - `COMPLETED`：所有 item 皆已處理（含部分失敗）
- 冪等設計：若重送相同 `id`，直接回傳現有記錄，不重複建立

### finalize_batch_items

- 主鍵：`id`（ULID）
- 外鍵：
  - `request_id -> finalize_batch_requests.id`
  - `order_id -> orders.order_id`
- `action` enum：`COMPLETED`、`CANCELLED`
- `status` enum：
  - `PENDING`：尚未處理
  - `SUCCESS`：處理成功，`finalized_at` 有值
  - `FAILED`：處理失敗，`error_code` 有值
- `error_code` 可能值：`ORDER_NOT_FOUND`、`ORDER_ALREADY_FINALIZED`

## 備註

- `coupon_wallet` 對應的是 `coupons` 的查詢投影，可依 `member_id`、`brand_id`、`status` 組合查詢，不需獨立建表。
- `get_member_brand_change_logs` API 若需回傳 `before_brand_ids` / `after_brand_ids`，應以同一 `request_id` 的 `member_brand_change_logs` 批次事件進行重建。
- `get_order` API 的 `events` 對應 `order_logs`；`coupons_used` 對應 `order_coupon_logs`。
