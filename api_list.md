---
title: API Scope List
permalink: /api-list/
---

# 樹配券 2.0 API List

## 文件目的
彙整樹配券 2.0 可能需要的 API，並依呼叫端區分。此文件先作為 API scope 清單，後續可依各 API 逐一拆成完整 API spec。

## Scope 原則
- 本次專案核心為「券加金」模式：用戶刷卡後，以點數兌換神坊發行的 coupon，並將 coupon 用於折抵本次刷卡消費。
- 樹配券平台前台端負責品牌瀏覽、使用者自動兌換設定、券夾與歷史紀錄查詢。
- 發卡主機端負責刷卡授權後建立訂單，以及請款完成或取消交易後完成訂單生命週期。
- 對帳 API 不在本次 project scope，會另起專案處理。

## 狀態標記

| 狀態 | 說明 |
| ---- | ---- |
| 已有 spec | 專案資料夾內已有對應 API spec 草稿 |
| 需新增 spec | 本次 scope 需要，但尚未建立完整 API spec |
| 可選 | 視前端或營運需求決定是否納入 |
| Scope 外 | 已確認不納入本次 project scope |

## 樹配券平台前台端

| API | Method | Endpoint | 用途 | 狀態 |
| ---- | ---- | ---- | ---- | ---- |
| `get_current_rotation` | `GET` | `/coupon/get_current_rotation` | 取得當前 active rotation 的設定（活動期間、品牌選擇上限、顯示用說明參數），及本檔期所有具備 active `auto` campaign 的品牌清單與 campaign 規則。 | 已有 spec |
| `activate_member` | `POST` | `/coupon/activate_member` | 用戶在 CR 前台同意啟用樹配券服務。神坊呼叫點數系統 API，成功後更新授權狀態並寫入 log。（原 `member_authorize`） | 已有 spec |
| `deactivate_member` | `POST` | `/coupon/deactivate_member` | 用戶在 CR 前台主動解除服務。神坊更新授權狀態並寫入 log；現有 coupon 保留但不可用。（原 `member_unauthorize`） | 已有 spec |
| `get_member_settings` | `GET` | `/coupon/get_member_settings` | 取得使用者目前的完整設定狀態，包含 `auto_redeem_enabled`、`max_selectable_auto_brand_count`、`last_changed_at`，以及目前已選擇、且當前仍具備 active `auto` campaign 的品牌。 | 已有 spec |
| `update_member_selected_brands` | `POST` | `/coupon/update_member_selected_brands` | 更新該會員的已選品牌清單。以 `brand_ids` 作為更新後完整結果，後端自行計算 diff 並寫入異動紀錄。 | 已有 spec |
| `update_member_auto_redeem_settings` | `POST` | `/coupon/update_member_auto_redeem_settings` | 切換該會員的自動兌換服務狀態（暫停／啟用）。`auto_redeem_enabled: boolean`。 | 已有 spec |
| ~~`update_member_settings`~~ | ~~`PATCH`~~ | ~~`/coupon/update_member_settings`~~ | ~~[DEPRECATED] 已拆分為 `update_member_selected_brands` 與 `update_member_auto_redeem_settings`~~ | ~~已有 spec~~ |
| `get_member_settings_change_logs` | `GET` | `/coupon/get_member_settings_change_logs` | 查詢使用者過去 1 年內的品牌選擇與自動兌換異動紀錄（`change_selected_brands`、`disable_auto_redeem`、`enable_auto_redeem`、`system_clear_brands`）。 | 已有 spec |
| `get_coupon_wallet` | `GET` | `/coupon/get_coupon_wallet` | 查詢使用者券夾品牌摘要，回傳當前 rotation 曾選過的所有品牌及各品牌可用券張數（`AVAILABLE` count）。 | 已有 spec |
| `get_coupons` | `GET` | `/coupon/get_coupons` | 查詢使用者券列表，預設回全部券狀態，並支援 `brand_id`、`status` 篩選。（原 `get_coupon_wallet`） | 已有 spec |
| `get_coupon_detail` | `GET` | `/coupon/get_coupon_detail` | 查詢單張券詳情，包含狀態、效期、折抵規則及兌換時所花費的點數。 | 已有 spec |
| `get_member_orders` | `GET` | `/coupon/get_member_orders` | 查詢使用者歷史折抵訂單列表，供用戶瀏覽折抵紀錄。 | 已有 spec |
| ~~`get_order`~~ | `GET` | `/coupon/get_order` | ⚠️ 已於 2026-07-08 廢除：前台不提供單筆訂單明細，改用 `get_member_orders`；發卡主機端單筆查詢由 `bank_get_order` 承接。 | 已廢除 |
| `preview_discount` | `POST` | `/coupon/preview_discount` | 在未建立訂單前，試算指定品牌與刷卡金額可能折抵多少。若前端不需要即時試算，可不做。 | 可選 |
| `redeem_manual_coupon`（暫定名） | `POST` | `/coupon/redeem_manual_coupon`（暫定） | 讓用戶對 `type=manual` 的 campaign 主動發起兌換，取得該 campaign 對應的 coupon。2026-07-01 調查發現：`get_current_rotation` 已回傳 `manual` campaign 規則供前端「手動換券頁面」顯示，但目前沒有任何 API 讓用戶實際執行兌換動作；兌換觸發方式、扣點時機等細節尚待確認。 | 需新增 spec |


## 發卡主機端 / 銀行信用卡系統

| API | Method | Endpoint | 用途 | 狀態 |
| ---- | ---- | ---- | ---- | ---- |
| `create_order` | `POST` | `/bank/create_order` | 信用卡授權後由發卡主機呼叫。神坊依 brand、用戶、刷卡金額執行清算，使用既有 coupon、扣點、即時發新 coupon，並保存卡號後四碼供後續前台查詢顯示。 | 已有 spec |
| `batch_finalize_orders` | `POST` | `/bank/batch_finalize_orders` | 商戶請款完成或取消交易後由發卡主機批次呼叫。以 CSV 檔案上傳多筆 `{order_id, action}`，神坊立即回 `202 Accepted`，實際處理以非同步方式執行。`request_id` 由發卡主機自行產生，相同 `request_id` 重送時回傳 `BATCH_REQUEST_ALREADY_EXISTS`。 | 已有 spec |
| `get_finalize_batch_status` | `GET` | `/bank/get_finalize_batch_status` | 發卡主機以 `request_id` 查詢批次 finalize 請求的整體狀態與各筆訂單的處理進度。 | 已有 spec |
| `bank_get_order` | `GET` | `/bank/get_order` | 發卡主機依 `order_id` 查詢訂單狀態與折抵金額，僅回傳銀行端必要欄位。 | 已有 spec |

### 發卡主機端說明
- `order_id` 由發卡主機編制，神坊直接以該 `order_id` 作為訂單主識別。
- 因 `order_id` 已由發卡主機編制，不需要額外提供 `get_order_by_issuer_ref`。
- 對帳相關 API 不納入本次 scope。

## 神坊後台 / 營運管理

| API | Method | Endpoint | 用途 | 狀態 |
| ---- | ---- | ---- | ---- | ---- |
| `get_member_authorization_logs` | `GET` | `/coupon/admin/get_member_authorization_logs` | 客服查詢指定用戶的授權異動歷史紀錄。 | 第二階段，out of scope |
| `get_brands` | `GET` | `/admin/get_brands` | 後台查詢合作品牌清單，包含啟用狀態、分類、logo、`treepoint_merchant_provider_key`、建立與更新時間。 | 第二階段，out of scope |
| `create_brand` | `POST` | `/admin/create_brand` | 建立合作品牌，需包含 `treepoint_merchant_provider_key`。 | 第二階段，out of scope |
| `update_brand` | `PATCH` | `/admin/update_brand` | 更新合作品牌基本資料、`treepoint_merchant_provider_key` 或啟用狀態。 | 第二階段，out of scope |
| `get_campaigns` | `GET` | `/admin/get_campaigns` | 查詢 campaign 清單與規則內容。 | 第二階段，out of scope |
| `create_campaign` | `POST` | `/admin/create_campaign` | 建立 campaign 規則，包含 `coupon_min_order_amount`、`coupon_redeem_points`、`coupon_discount_amount`、`max_redemptions_per_order`、`start_at`、`end_at`。 | 第二階段，out of scope |
| `update_campaign` | `PATCH` | `/admin/update_campaign` | 更新 campaign 規則與生效區間，包含 `coupon_min_order_amount`、`coupon_redeem_points`、`coupon_discount_amount`、`max_redemptions_per_order`、`start_at`、`end_at`；active 狀態由當前時間是否落在生效區間內決定。 | 第二階段，out of scope |

## 神坊內部服務 / Batch Job

| API / Job | 觸發方 | 用途 | 狀態 |
| ---- | ---- | ---- | ---- |
| `issue_coupon` | Coupon service | 點數扣除後建立新 coupon，初始狀態為 `consumed`。 | 需依架構確認 |
| `batch_create_brands` | Internal CLI | 以批次檔或設定檔一次建立多筆 brand 主資料，作為後台大量上架品牌的內部工具。 | CLI，不開發為 API |
| `batch_update_brands` | Internal CLI | 以批次檔或設定檔一次更新多筆 brand 主資料，例如名稱、分類、logo、`treepoint_merchant_provider_key` 或啟用狀態。 | CLI，不開發為 API |
| `batch_create_campaigns` | Internal CLI | 以批次檔或設定檔一次建立多筆 campaign 規則，供營運大量上架活動使用，欄位包含 `max_redemptions_per_order`。 | CLI，不開發為 API |
| `batch_update_campaigns` | Internal CLI | 以批次檔或設定檔一次更新多筆 campaign 規則或生效區間，包含 `max_redemptions_per_order`、`start_at`、`end_at`。 | CLI，不開發為 API |
| `expire_coupons` | Batch job | 定期將超過有效期限的 `available` coupon 改為 `expired`。 | 需新增 job |
| `lazy_clear_member_selected_brands` | 由 API 觸發（`get_member_selected_brands`、`update_member_selected_brands`、`create_order` 等） | 當用戶進入系統時，檢查其 `member_selected_brands.rotation_key` 是否與當前 active rotation 相符。若不符，代表舊檔期選擇已失效：刪除舊選擇並為每個被清除的品牌寫入一筆 `SYSTEM_CLEAR_BRANDS` 事件（`occurred_at` = 舊 rotation 的 `end_time`）。 | 需新增邏輯 |

### 系統環境參數說明
- `coupon_valid_days` 為全域有效天數參數，供發券時計算 `coupon.expired_at`；不屬於 `campaign` 欄位。
- `max_selectable_auto_brand_count`（原 `max_selectable_brand_count`）已移至 `rotations` 表，由各檔期自行定義，不再是全域 `system_configs` 參數。
- `display_coupon_min_order_amount` / `display_coupon_redeem_points` 設置於 `rotations` 表，目前供前端呈現說明文字，不影響清算；未來後台有 campaign 建立介面時，將作為新建 campaign 的 default value。

### 訂單資料模型說明
- DB layer 的訂單歷程表使用 `order_logs`
- DB layer 的訂單用券快照表使用 `order_coupon_items`
- API response 可維持 `events` / `coupons_used` 作為對外欄位名稱

## 本次 Scope 外

| API | 原因 |
| ---- | ---- |
| `get_order_by_issuer_ref` | 不需要。`order_id` 由發卡主機編制，發卡主機與神坊可共同使用該識別查詢訂單。 |
| `get_reconciliation_orders` | 不納入本次 project scope。對帳所需 API 會另起專案處理。 |
| `get_settlement_report` | 屬於對帳 / 結算領域，暫不納入本次 project scope。 |
