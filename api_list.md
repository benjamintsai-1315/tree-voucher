---
title: API Scope List
permalink: /api-list/
---

# 樹享券 2.0 API List

## 文件目的
彙整樹享券 2.0 可能需要的 API，並依呼叫端區分。此文件先作為 API scope 清單，後續可依各 API 逐一拆成完整 API spec。

## Scope 原則
- 本次專案核心為「券加金」模式：用戶刷卡後，以點數兌換神坊發行的 coupon，並將 coupon 用於折抵本次刷卡消費。
- 樹享券平台前台端負責品牌瀏覽、使用者自動兌換設定、券夾與歷史紀錄查詢。
- 發卡主機端負責刷卡授權後建立訂單，以及請款完成或取消交易後完成訂單生命週期。
- 對帳 API 不在本次 project scope，會另起專案處理。

## 狀態標記
| 狀態 | 說明 |
| ---- | ---- |
| 已有 spec | 專案資料夾內已有對應 API spec 草稿 |
| 需新增 spec | 本次 scope 需要，但尚未建立完整 API spec |
| 可選 | 視前端或營運需求決定是否納入 |
| Scope 外 | 已確認不納入本次 project scope |

## 樹享券平台前台端

| API | Method | Endpoint | 用途 | 狀態 |
| ---- | ---- | ---- | ---- | ---- |
| `get_active_brands` | `GET` | `/coupon/get_active_brands` | 取得目前所有具備 active campaign 的品牌清單及 campaign 規則，供品牌一覽頁呈現。 | 已有 spec |
| `user_authorize` | `POST` | `/coupon/user_authorize` | 記錄使用者已同意樹享券平台可使用其點數，作為後續自動兌換與用點清算的前置授權。 | 已有 spec |
| `get_user_selected_brands` | `GET` | `/coupon/get_user_selected_brands` | 取得使用者目前的品牌設定狀態，包含 `auto_redeem_enabled`，以及目前已選擇、且當前仍具備 active campaign 的品牌。 | 已有 spec |
| `update_user_selected_brands` | `POST` 或 `PATCH` | `/coupon/update_user_selected_brands` | 對標 `get_user_selected_brands`，統一處理使用者已選品牌設定異動，包含首次選品牌、更換品牌、暫停用券、重啟用券。 | 已有 spec |
| `get_user_brand_change_logs` | `GET` | `/coupon/get_user_brand_change_logs` | 查詢使用者過去 1 年內的品牌選擇與自動兌換異動紀錄。 | 已有 spec |
| `get_coupon_wallet` | `GET` | `/coupon/get_coupon_wallet` | 查詢使用者券夾列表，預設回全部券狀態，並支援 `brand_id`、`status` 篩選。 | 已有 spec |
| `get_user_orders` | `GET` | `/coupon/get_user_orders` | 查詢使用者歷史折抵訂單列表，供用戶瀏覽折抵紀錄。 | 已有 spec |
| `get_order` | `GET` | `/coupon/get_order` | 查詢單筆訂單完整資訊，包含折抵明細與事件歷程。 | 已有 spec |
| `preview_discount` | `POST` | `/coupon/preview_discount` | 在未建立訂單前，試算指定品牌與刷卡金額可能折抵多少。若前端不需要即時試算，可不做。 | 可選 |

### `update_user_selected_brands` action 建議

| action | 用途 | 主要參數 | 商務規則 |
| ---- | ---- | ---- | ---- |
| `SELECT_BRANDS` | 首次選擇或更換自動兌換品牌 | `user_id`, `after_brand_ids` | 需檢查每人最多選擇品牌數、每自然月更換次數、品牌是否有 active campaign。 |
| `PAUSE` | 暫停自動用券 | `user_id` | 暫停後使用者已選品牌可保留，但刷卡時不觸發自動兌換。 |
| `RESUME` | 重啟自動用券 | `user_id` | 重啟時需確認使用者仍有已選品牌，且至少一個品牌仍有 active campaign。 |

## 發卡主機端 / 銀行信用卡系統

| API | Method | Endpoint | 用途 | 狀態 |
| ---- | ---- | ---- | ---- | ---- |
| `create_order` | `POST` | `/coupon/create_order` | 信用卡授權後由發卡主機呼叫。神坊依 brand、用戶、刷卡金額執行清算，使用既有 coupon、扣點、即時發新 coupon，並保存卡號後四碼供後續前台查詢顯示。 | 已有 spec |
| `finalize_order` | `POST` | `/coupon/finalize_order` | 商戶請款完成或取消交易後由發卡主機非同步呼叫。請款成功時 coupon `processing -> completed`；取消時依是否已到期轉為 `available` 或 `expired`，點數不返還。 | 已有 spec |
| `get_order` | `GET` | `/coupon/get_order` | 發卡主機依 `order_id` 查詢單筆訂單狀態、折抵明細與事件歷程。 | 已有 spec |

### 發卡主機端說明
- `order_id` 由發卡主機編制，神坊直接以該 `order_id` 作為訂單主識別。
- 因 `order_id` 已由發卡主機編制，不需要額外提供 `get_order_by_issuer_ref`。
- 對帳相關 API 不納入本次 scope。

## 神坊後台 / 營運管理

| API | Method | Endpoint | 用途 | 狀態 |
| ---- | ---- | ---- | ---- | ---- |
| `get_brands` | `GET` | `/coupon/admin/get_brands` | 後台查詢合作品牌清單，包含啟用狀態、分類、logo、`treepoint_merchant_provider_key`、建立與更新時間。 | 第二階段，out of scope |
| `create_brand` | `POST` | `/coupon/admin/create_brand` | 建立合作品牌，需包含 `treepoint_merchant_provider_key`。 | 第二階段，out of scope |
| `update_brand` | `PATCH` | `/coupon/admin/update_brand` | 更新合作品牌基本資料、`treepoint_merchant_provider_key` 或啟用狀態。 | 第二階段，out of scope |
| `get_stores` | `GET` | `/coupon/admin/get_stores` | 查詢 brand 底下實體門店或特店識別資料，用於刷卡交易對應 brand。 | 第二階段，out of scope |
| `create_store` | `POST` | `/coupon/admin/create_store` | 建立 brand 底下門店或特店識別資料。 | 第二階段，out of scope |
| `update_store` | `PATCH` | `/coupon/admin/update_store` | 更新門店或特店識別資料。 | 第二階段，out of scope |
| `get_campaigns` | `GET` | `/coupon/admin/get_campaigns` | 查詢 campaign 清單與規則內容。 | 第二階段，out of scope |
| `create_campaign` | `POST` | `/coupon/admin/create_campaign` | 建立 campaign 規則，包含 `unit_cash_amount`、`unit_point_amount`、`unit_discount_amount`、`start_at`、`end_at`。 | 第二階段，out of scope |
| `update_campaign` | `PATCH` | `/coupon/admin/update_campaign` | 更新 campaign 規則與生效區間，包含 `unit_cash_amount`、`unit_point_amount`、`unit_discount_amount`、`start_at`、`end_at`；active 狀態由當前時間是否落在生效區間內決定。 | 第二階段，out of scope |

## 神坊內部服務 / Batch Job

| API / Job | 觸發方 | 用途 | 狀態 |
| ---- | ---- | ---- | ---- |
| `issue_coupon` | Coupon service | 點數扣除後建立新 coupon，初始狀態為 `processing`。 | 需依架構確認 |
| `batch_create_brands` | Internal CLI | 以批次檔或設定檔一次建立多筆 brand 主資料，作為後台大量上架品牌的內部工具。 | CLI，不開發為 API |
| `batch_update_brands` | Internal CLI | 以批次檔或設定檔一次更新多筆 brand 主資料，例如名稱、分類、logo、`treepoint_merchant_provider_key` 或啟用狀態。 | CLI，不開發為 API |
| `batch_create_campaigns` | Internal CLI | 以批次檔或設定檔一次建立多筆 campaign 規則，供營運大量上架活動使用。 | CLI，不開發為 API |
| `batch_update_campaigns` | Internal CLI | 以批次檔或設定檔一次更新多筆 campaign 規則或生效區間，包含 `start_at`、`end_at`。 | CLI，不開發為 API |
| `expire_coupons` | Batch job | 定期將超過有效期限的 `available` coupon 改為 `expired`。 | 需新增 job |

### 系統環境參數說明
- `coupon_valid_days` 為全域有效天數參數，供發券時計算 `coupon.expired_at`；不屬於 `campaign` 欄位。

## 本次 Scope 外

| API | 原因 |
| ---- | ---- |
| `get_order_by_issuer_ref` | 不需要。`order_id` 由發卡主機編制，發卡主機與神坊可共同使用該識別查詢訂單。 |
| `get_reconciliation_orders` | 不納入本次 project scope。對帳所需 API 會另起專案處理。 |
| `get_settlement_report` | 屬於對帳 / 結算領域，暫不納入本次 project scope。 |
