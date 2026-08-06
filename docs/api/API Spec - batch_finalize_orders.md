---
title: API Spec - batch_finalize_orders
permalink: /api-specs/batch-finalize-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-06 | 依 2026-07-21 PDF 版本核對後訂正：權限邊界恢復「來源 IP 白名單」檢查（連動擴大至所有 `/bank/...` API，見 CLAUDE.md 同步修改）；非同步處理架構改回沿用 S3 落地原始檔（`tree_coupon_{env}_s3/orders/finalize_requests/{request_id}.ndjson`）＋ background job 以 100 行為一 chunk 處理＋ `finalize_requests`／`finalize_request_order_items` 表名＋ `success_count`/`error_count`/`total_count` 完成判定＋ Batch-level error 段落＋ `coupon_event_logs` 稽核紀錄，取代 2026-07-30 版本的取消設計；保留 2026-07-30「同步階段即逐行建立 item」的做法——檔案上傳至 S3 後不等 background job，同步解析每一行並建立 `finalize_request_order_items`，無法解析者（不合法 JSON／缺必要欄位／欄位過長）以合併後的單一 `FILE_PARSE_ERROR` 標記（取代原 `INVALID_JSON`／`INVALID_PAYLOAD` 兩碼），不進入非同步佇列；`DUPLICATE_ORDER_ID`、`INVALID_ACTION` 維持於非同步階段判定；Response body 改回 `{}`；`request_id`／`order_id` 恢復「僅限英數字與底線」與「全系統唯一」限制；422／413 錯誤分類恢復為 PDF 版本（`request_id`／`orders` 內容驗證為 422，`FILE_SIZE_EXCEEDED` 為 413），移除 `BATCH_REQUEST_ID_REQUIRED`／`ORDERS_FILE_REQUIRED` 400 錯誤碼 |
| 2026-07-30 | 同步驗證移除 orders 檔案內容可解析性檢查，改為逐行建立 finalize_batch_items——不論該行是否可解析／order_id 是否存在／訂單狀態為何，皆建立一筆 item；無法解析的行（不合法 JSON、缺必要欄位、欄位過長）以 raw_data 保存原始內容，order_id／action 留空，直接標記 FAILED + error_code=FILE_PARSE_ERROR，不進入非同步佇列；取消獨立 result file 設計，DB table 為唯一結果來源；ORDER_NOT_FOUND 定義收斂為單純查無此 order_id，新增 ORDER_NOT_FINALIZABLE（訂單存在但狀態為 pending）與 ORDER_FAILED（訂單存在但狀態為 error），ORDER_ALREADY_FINALIZED 定義不變（completed／cancelled）；422 FILE_PARSE_ERROR 自 request-level 移除（2026-08-06 起：item 建立時機與 FILE_PARSE_ERROR 合併命名部分保留，其餘非同步架構已改回 PDF 版本，見上方 2026-08-06 條目） |
| 2026-07-21 | Request 格式改回 `multipart/form-data` + JSON Lines（ndjson）：`request_id` 為 text part，`orders` 為 file part（每行一筆訂單物件）；銀行端可於記憶體中逐行組出 ndjson 傳輸，不需落地實體檔案。移除單批 1000 筆上限，改以**檔案大小 < 10MB** 為批次基準，`request_id` 對應同一份檔案固定不變 |
| 2026-07-21 | API 同步驗證範圍限縮為三項：`request_id` 冪等驗證、file size 檢查、file 內容可解析性檢查；`INVALID_ACTION` 改列為非同步 item-level 錯誤（與 `ORDER_NOT_FOUND`、`ORDER_ALREADY_FINALIZED` 同層級處理），不再於同步階段擋下整批次 |
| 2026-07-21 | `orders[].action` 請求欄位值統一改為小寫 `complete` \| `cancel`（原 `COMPLETED` \| `CANCELLED`），使用情境段落標題與 Request Sample 一併同步 |
| 2026-07-13 | 明訂 `action = CANCELLED` 時訂單 `discount_amount` 歸零（前台 `get_member_orders` 以 `discount_amount = 0` + `order_status = cancelled` 判斷顯示「已退回券匣」） |
| 2026-07-13 | `order.status` 實際 DB 欄位值校正為五態：`waiting_finalization` 更名為 `processing`、`failed` 更名為 `error` |
| 2026-07-08 | 補述訂單狀態銜接：終結前置為 `order.status = waiting_finalization`，COMPLETED → `completed`、CANCELLED → `cancelled`；釐清 `ORDER_NOT_FOUND`（含不可終結的 `failed` 訂單）與 `ORDER_ALREADY_FINALIZED`（已為 `completed`/`cancelled`）判定 |
| 2026-07-06 | 冪等統一：相同 `request_id` 一律回 `400 BATCH_REQUEST_ALREADY_EXISTS`；修正內文「冪等設計」誤述為直接回傳原批次接收資訊 |
| 2026-06-25 | `BATCH_SIZE_EXCEEDED`、`INVALID_ACTION` 改為 422（語意驗證錯誤，與格式錯誤的 400 區分） |
| 2026-06-25 | Response 改為 `200 OK` no body — `accepted_count` 無附加資訊（發卡主機自知筆數）；`submitted_at` 可由 `get_finalize_batch_status` 查詢；`request_id` 由發卡主機自行編列，回傳無意義（2026-08-06 起：Response body 恢復為 `{}`，見上方 2026-08-06 條目） |
| 2026-06-24 | 改為 JSON body（`application/json`）；`request_id` 改名為 `request_id`；新增單批次上限 1000 筆（超過回 `BATCH_SIZE_EXCEEDED`）；移除 CSV 上傳設計；建議銀行端每批 500–1000 筆分批打入 |
| 2026-06-22 | Response HTTP status 改為 `200 OK` |
| 2026-06-16 | 由 `finalize_order` 更名為 `batch_finalize_orders`；輸入改為 CSV 檔案上傳（`multipart/form-data`）；冪等設計改為相同 `request_id` 直接回 `BATCH_REQUEST_ALREADY_EXISTS` |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled` |
| 2026-06-16 | 改為批次接收、非同步處理；response 改為 `202 Accepted`（後改為 `200 OK`） |
| 2026-06-15 | Endpoint 改為 `/bank/finalize_order`（原 `/coupon/finalize_order`），依呼叫端分類路徑 |

# API: batch_finalize_orders

## 功能說明
讓發卡主機在商戶請款完成或申請退刷後，以 `multipart/form-data`（訂單資料採 JSON Lines / ndjson 格式）批次傳入訂單結案通知。神坊完成請求驗證、原始檔案上傳至 S3 及逐行建立處理項目後回應 `200 OK`，實際訂單狀態轉換以非同步方式（background job）執行。發卡主機可透過 `get_finalize_batch_status` 查詢各筆訂單的處理進度。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - 來源 IP 需在白名單內
    - note: API Key 與 IP 白名單皆存於 AWS Parameter Store

## 使用情境

### 請款完成（complete）
- 商戶向銀行請款後，發卡主機批次通知神坊
- 神坊（非同步）將該訂單所有 `consumed` 券改為 `settled`
- 神坊執行代償流程
- 訂單狀態 `order.status` 由 `processing` 推進為 `completed`

### 退刷（cancel）
- 商戶向銀行申請刷退後，發卡主機批次通知神坊
- 神坊（非同步）將該訂單所有 `consumed` 券依是否到期轉為 `available` 或 `expired`
- 點數不返還
  - 退回且尚未到期的券成為後續可使用的舊券；已到期的券更新為 `expired`
- 訂單狀態 `order.status` 由 `processing` 推進為 `cancelled`，同時訂單 `discount_amount` 歸零（本次折抵取消，前台據此顯示「已退回券匣」）

### 冪等設計
- `request_id` 由發卡主機自行產生並帶入，用於識別批次請求
- 若相同 `request_id` 再次呼叫，神坊回 `400 BATCH_REQUEST_ALREADY_EXISTS`，不重複建立或重跑

### 檔案大小限制
- 不再依筆數固定切批，改以**單次傳輸的檔案大小 < 10MB** 為基準，超過回 `413 FILE_SIZE_EXCEEDED`
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
| request_id | text field | TRUE | 最多 36 字；由發卡主機自行產生，用於冪等識別；僅限英數字與底線；全系統唯一 |
| orders | file（Content-Type: `application/x-ndjson`） | TRUE | JSON Lines 格式，每行一筆獨立完整的訂單物件；檔案大小需 < 10MB |

### orders 檔案內容欄位（每行一筆 JSON 物件）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| order_id | string | TRUE | 訂單識別碼，最多 50 字；僅限英數字與底線；全系統唯一 |
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

## Response body
```json
{}
```

### 邏輯說明

#### 同步處理流程
- 神坊收到請求後，依序驗證：
  1. `request_id` 冪等性（DB 透過 UNIQUE constraint 保證不重複；若相同 `request_id` 已存在，回 `400 BATCH_REQUEST_ALREADY_EXISTS`，不重複建立或執行批次）
  2. `orders` file size 是否 < 10MB（超過回 `413 FILE_SIZE_EXCEEDED`）
- 全部驗證通過後，建立 `finalize_requests`，初始狀態為 `receiving`
- 原始檔案上傳至 S3：`tree_coupon_{env}_s3/orders/finalize_requests/{request_id}.ndjson`
  - 若接收或上傳期間發生錯誤：清理本次請求已建立但尚未成立的批次資料及檔案，不建立 item、不排入 background job；若對應紀錄已於失敗清理時刪除，修正問題後可用相同 `request_id` 重新上傳，若 `request_id` 原本已存在則須改用新的 `request_id`
- 原始檔案成功上傳至 S3 後，**同步逐行解析**並建立 `finalize_request_order_items`（保存 `line_no`、`raw_data`）：
  - 該行可正確解析（合法 JSON 且含 `order_id`、`action`）：寫入 `order_id`、`action`，初始狀態 `pending`
  - 該行無法正確解析（非合法 JSON、缺必要欄位、或欄位長度超過上限）：狀態直接標記為 `error`，`error_type = FILE_PARSE_ERROR`，不進入非同步處理
- `finalize_requests.status` 由 `receiving` 更新為 `pending`，並設定 `total_count`（＝本批次總行數）
- 排入 background job，回傳 `200 OK`。僅表示請求驗證、原始檔案上傳及 item 建立完成；實際訂單結案結果由非同步流程處理

#### 非同步處理
- Background job 開始執行時，將 `finalize_requests.status` 更新為 `processing`，並設定 `started_at`
- 僅處理狀態為 `pending` 的 item，依 `line_no` 以每 100 行為一個 chunk 逐行處理
- 單行處理規則：
  - `order_id` 重複：以第一筆格式合法的資料為有效項目，後續資料不執行結案，item 設為 `error`，並記錄 `DUPLICATE_ORDER_ID`
  - `action` 值不合法（非 `complete` \| `cancel`）：item 設為 `error`，記錄 `INVALID_ACTION`
  - 通過上述檢查：依 `order_id` 查詢訂單並檢查 `order.status`：
    - 查無此 `order_id`：`ORDER_NOT_FOUND`
    - 訂單存在、狀態為 `completed` / `cancelled`：`ORDER_ALREADY_FINALIZED`（已為終態，不重複處理）
    - 訂單存在、狀態為 `pending`：`ORDER_NOT_FINALIZABLE`（清算尚未完成，不可結案）
    - 訂單存在、狀態為 `error`：`ORDER_FAILED`（先前 `create_order` 清算失敗，無法執行結案）
    - 訂單存在、狀態為 `processing`（唯一可終結狀態）：執行訂單結案邏輯
      - `action = complete`：訂單狀態由 `processing` 更新為 `completed`，並設定 `finalized_at`；對應 `consumed` 券更新為 `settled`、`settle_order_id={order_id}`；每張被更新的 coupon 各新增一筆 `type=settled` 的 `coupon_event_logs`
      - `action = cancel`：訂單狀態由 `processing` 更新為 `cancelled`、`discount_amount` 歸零，並設定 `finalized_at`；對應 `consumed` 券依處理當下是否到期，更新為 `available` 或 `expired`，點數不返還；每張被更新的 coupon 各新增一筆 `coupon_event_logs`（券轉為 `available` 時 `type=reverted`；轉為 `expired` 時 `type=expired`）
  - 成功時 item 更新為 `success` 並設定 `finalized_at`；失敗時 item 更新為 `error` 並記錄對應 `error_type`
  - 單筆失敗不會中斷整批處理
- 每完成一個 chunk，依完成的 item 結果更新 `finalize_requests` 的 `success_count`、`error_count`
- 所有輸入行處理完成，且符合 `total_count = success_count + error_count` 條件時，將 `finalize_requests.status` 更新為 `completed`，並設定 `completed_at`
  - `completed` 表示所有輸入行都已產生最終結果，不代表每一筆訂單都處理成功
  - 單行格式錯誤或訂單處理失敗不屬於 batch-level error，會記錄於對應的 item，並繼續處理下一行

#### Batch-level error
若 background job 發生無法繼續處理整份檔案的系統性錯誤：
- 記錄錯誤並發送告警
- 批次狀態恢復為 `pending`
- 不自動重試，待確認問題後由人工重新排程（已完成的訂單項目不重複執行）

## 422 錯誤回傳（語意驗證）
1. `request_id` 未提供
2. `request_id` 為空字串、超過 36 字元，或包含英數字與底線以外的字元
3. `orders` file 未提供
4. `orders` 內容為空

## 413 錯誤回傳（Content too large）
1. `orders` 檔案大小超過限制：`FILE_SIZE_EXCEEDED`

## 400 錯誤回傳（MESSAGE: TYPE）

| TYPE | DEFAULT_MSG | 說明 |
| ---- | ---- | ---- |
| BATCH_REQUEST_ALREADY_EXISTS | 批次請求已存在 | 相同 `request_id` 已存在 |
| UPLOAD_FILE_FAILED | 檔案上傳失敗 | S3 上傳或後續同步流程發生非預期錯誤 |

> item-level 錯誤（`FILE_PARSE_ERROR`、`DUPLICATE_ORDER_ID`、`INVALID_ACTION`、`ORDER_NOT_FOUND`、`ORDER_NOT_FINALIZABLE`、`ORDER_ALREADY_FINALIZED`、`ORDER_FAILED`）不影響整批次的 HTTP 回應，記錄於對應 item 的 `error_type`，見上方「邏輯說明」。
