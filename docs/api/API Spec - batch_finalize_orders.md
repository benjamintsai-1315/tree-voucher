---
title: API Spec - batch_finalize_orders
permalink: /api-specs/batch-finalize-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-21 | Request 格式改回 `multipart/form-data` + JSON Lines（ndjson）：`request_id` 為 text part，`orders` 為 file part（每行一筆訂單物件）；銀行端可於記憶體中逐行組出 ndjson 傳輸，不需落地實體檔案。移除單批 1000 筆上限，改以**檔案大小 < 10MB** 為批次基準，`request_id` 對應同一份檔案固定不變 |
| 2026-07-21 | API 同步驗證範圍限縮為三項：`request_id` 冪等驗證、file size 檢查、file 內容可解析性檢查；`INVALID_ACTION` 改列為非同步 item-level 錯誤（與 `ORDER_NOT_FOUND`、`ORDER_ALREADY_FINALIZED` 同層級處理），不再於同步階段擋下整批次 |
| 2026-07-21 | `orders[].action` 請求欄位值統一改為小寫 `complete` \| `cancel`（原 `COMPLETED` \| `CANCELLED`），使用情境段落標題與 Request Sample 一併同步 |
| 2026-07-13 | 明訂 `action = CANCELLED` 時訂單 `discount_amount` 歸零（前台 `get_member_orders` 以 `discount_amount = 0` + `order_status = cancelled` 判斷顯示「已退回券匣」） |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`、`failed` 更名為 `error` |
| 2026-07-08 | 補述訂單狀態銜接：終結前置為 `order.status = waiting_finalization`，COMPLETED → `completed`、CANCELLED → `cancelled`；釐清 `ORDER_NOT_FOUND`（含不可終結的 `failed` 訂單）與 `ORDER_ALREADY_FINALIZED`（已為 `completed`/`cancelled`）判定 |
| 2026-07-06 | 冪等統一：相同 `request_id` 一律回 `400 BATCH_REQUEST_ALREADY_EXISTS`；修正內文「冪等設計」誤述為直接回傳原批次接收資訊 |
| 2026-06-25 | `BATCH_SIZE_EXCEEDED`、`INVALID_ACTION` 改為 422（語意驗證錯誤，與格式錯誤的 400 區分） |
| 2026-06-25 | Response 改為 `200 OK` no body — `accepted_count` 無附加資訊（發卡主機自知筆數）；`submitted_at` 可由 `get_finalize_batch_status` 查詢；`request_id` 由發卡主機自行編列，回傳無意義 |
| 2026-06-24 | 改為 JSON body（`application/json`）；`request_id` 改名為 `request_id`；新增單批次上限 1000 筆（超過回 `BATCH_SIZE_EXCEEDED`）；移除 CSV 上傳設計；建議銀行端每批 500–1000 筆分批打入 |
| 2026-06-22 | Response HTTP status 改為 `200 OK` |
| 2026-06-16 | 由 `finalize_order` 更名為 `batch_finalize_orders`；輸入改為 CSV 檔案上傳（`multipart/form-data`）；冪等設計改為相同 `request_id` 直接回 `BATCH_REQUEST_ALREADY_EXISTS` |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled` |
| 2026-06-16 | 改為批次接收、非同步處理；response 改為 `202 Accepted`（後改為 `200 OK`） |
| 2026-06-15 | Endpoint 改為 `/bank/finalize_order`（原 `/coupon/finalize_order`），依呼叫端分類路徑 |

# API: batch_finalize_orders

## 功能說明
讓發卡主機在商戶請款完成或申請退刷後，以 `multipart/form-data`（訂單資料採 JSON Lines / ndjson 格式）批次傳入訂單結案通知。神坊收到請求後立即回應 `200 OK`，實際狀態轉換以非同步方式執行。發卡主機可透過 `get_finalize_batch_status` 查詢各筆訂單的處理進度。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權

## 使用情境

### 請款完成（complete）
- 商戶向銀行請款後，發卡主機批次通知神坊
- 神坊（非同步）將該訂單所有 `consumed` 券改為 `settled`
- 神坊執行代償流程
- 訂單狀態 `order.status` 由 `processing` 推進為 `completed`

### 退刷（cancel）
- 商戶向銀行申請刷退後，發卡主機批次通知神坊
- 神坊（非同步）將該訂單所有 `consumed` 券依是否到期轉為 `available` 或 `expired`
- 點數不返還；退回的券成為後續可用的舊券
- 訂單狀態 `order.status` 由 `processing` 推進為 `cancelled`，同時訂單 `discount_amount` 歸零（本次折抵取消，前台據此顯示「已退回券匣」）

### 冪等設計
- `request_id` 由發卡主機自行產生並帶入，用於識別批次請求
- 若相同 `request_id` 再次呼叫，神坊回 `400 BATCH_REQUEST_ALREADY_EXISTS`，不重複建立或重跑

### 檔案大小限制
- 不再依筆數固定切批，改以**單次傳輸的檔案大小 < 10MB** 為基準，超過回 `FILE_SIZE_EXCEEDED`
- `request_id` 對應同一份檔案（同一批次），固定不變；發卡主機自行控制單一檔案內筆數，只要檔案大小落在門檻內即可一次送出
- 每批收到 `200 OK` 即可繼續下一批，不需等待非同步處理完成

# Request
HTTP method: `POST`
Endpoint: `/bank/batch_finalize_orders`
Content-Type: `multipart/form-data`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{issuer_api_key}}` |

## Request Parameters
（multipart/form-data parts）

| Part name | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| request_id | text field | TRUE | 最多 36 字；由發卡主機自行產生，用於冪等識別；建議格式：`BATCH_YYYYMMDD_序號` |
| orders | file（Content-Type: `application/x-ndjson`） | TRUE | JSON Lines 格式，每行一筆獨立完整的訂單物件；檔案大小需 < 10MB |

### orders 檔案內容欄位（每行一筆 JSON 物件）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| order_id | string | TRUE | 訂單識別碼，最多 50 字 |
| action | string | TRUE | 僅接受 `complete` \| `cancel` |

## Request Sample（multipart/form-data）

```
--boundary123
Content-Disposition: form-data; name="request_id"

BATCH_20261003_001
--boundary123
Content-Disposition: form-data; name="orders"; filename="orders.ndjson"
Content-Type: application/x-ndjson

{"order_id": "ORD_20261001_00001", "action": "complete"}
{"order_id": "ORD_20261001_00002", "action": "cancel"}
--boundary123--
```

# Response
HTTP Status: `200 OK`
Body: 無

### 邏輯說明
- 神坊收到請求後，同步依序檢查：
  1. `request_id` 冪等驗證
  2. file size 是否 < 10MB
  3. `orders` 檔案內容是否可正確解析（每行需為合法 JSON 物件，且含 `order_id`、`action` 必要欄位）
- 上述三項通過後，建立 `finalize_batch_requests` 記錄，並逐行建立 `finalize_batch_items`（初始狀態 `PENDING`），立即回傳 `200`
- 非同步 worker 處理各筆 item；每筆先確認 `action` 為合法值（`complete` \| `cancel`）、`order.status = processing`（唯一可終結狀態），再沿用原本的狀態轉換邏輯：
  - `action = complete`：所有對應券 `consumed → settled`，觸發代償流程，`order.status → completed`
  - `action = cancel`：`consumed` 券依是否到期轉為 `available` 或 `expired`，點數不返還，`order.status → cancelled`，訂單 `discount_amount` 歸零（與券狀態轉換同一 transaction）
- 單筆驗證失敗不中斷整批次，錯誤記錄於該 item 的 `error_code`：
  - `INVALID_ACTION`：`action` 值不合法（非同步逐筆檢查，不於同步階段擋下整批次）
  - `ORDER_NOT_FOUND`：查無此 `order_id`（含 `error` 訂單，因其不可終結）
  - `ORDER_ALREADY_FINALIZED`：訂單已為終態（`completed` / `cancelled`），不重複處理

## 400 錯誤回傳（request-level）
1. `request_id` 未提供：`BATCH_REQUEST_ID_REQUIRED`
2. `orders` file 未提供或內容為空：`ORDERS_FILE_REQUIRED`
3. 相同 `request_id` 已存在：`BATCH_REQUEST_ALREADY_EXISTS`

## 422 錯誤回傳（語意驗證）
1. `orders` 檔案大小超過 10MB：`FILE_SIZE_EXCEEDED`
2. `orders` 檔案內容無法正確解析（非合法 ndjson 格式，例如某行非合法 JSON 或缺必要欄位）：`FILE_PARSE_ERROR`
