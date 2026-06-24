---
title: API Spec - batch_finalize_orders
permalink: /api-specs/batch-finalize-orders/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-24 | 改為 JSON body（`application/json`）；`request_id` 改名為 `request_id`；新增單批次上限 1000 筆（超過回 `BATCH_SIZE_EXCEEDED`）；移除 CSV 上傳設計；建議銀行端每批 500–1000 筆分批打入 |
| 2026-06-22 | Response HTTP status 改為 `200 OK` |
| 2026-06-16 | 由 `finalize_order` 更名為 `batch_finalize_orders`；輸入改為 CSV 檔案上傳（`multipart/form-data`）；冪等設計改為相同 `request_id` 直接回 `BATCH_REQUEST_ALREADY_EXISTS` |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled` |
| 2026-06-16 | 改為批次接收、非同步處理；response 改為 `202 Accepted`（後改為 `200 OK`） |
| 2026-06-15 | Endpoint 改為 `/bank/finalize_order`（原 `/coupon/finalize_order`），依呼叫端分類路徑 |

# API: batch_finalize_orders

## 功能說明
讓發卡主機在商戶請款完成或申請退刷後，以 JSON 批次傳入訂單結案通知。神坊收到請求後立即回應 `200 OK`，實際狀態轉換以非同步方式執行。發卡主機可透過 `get_finalize_batch_status` 查詢各筆訂單的處理進度。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權

## 使用情境

### 請款完成（COMPLETED）
- 商戶向銀行請款後，發卡主機批次通知神坊
- 神坊（非同步）將該訂單所有 `consumed` 券改為 `settled`
- 神坊執行代償流程

### 退刷（CANCELLED）
- 商戶向銀行申請刷退後，發卡主機批次通知神坊
- 神坊（非同步）將該訂單所有 `consumed` 券依是否到期轉為 `available` 或 `expired`
- 點數不返還；退回的券成為後續可用的舊券

### 冪等設計
- `request_id` 由發卡主機自行產生並帶入，用於識別批次請求
- 若相同 `request_id` 再次呼叫，神坊直接回傳原批次接收資訊，不重複建立或重跑

### 分批建議
- 單次請求上限為 **1000 筆**，超過回 `BATCH_SIZE_EXCEEDED`
- 建議發卡主機資訊系統將當日訂單每 **500–1000 筆切一批**，各自帶不同 `request_id` 連續打入
- 每批收到 `200 OK` 即可繼續下一批，不需等待非同步處理完成

# Request
HTTP method: `POST`
Endpoint: `/bank/batch_finalize_orders`
Content-Type: `application/json`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{issuer_api_key}}` |

## Request Parameters
（body）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| request_id | string | TRUE | 最多 64 字；由發卡主機自行產生，用於冪等識別；建議格式：`BATCH_YYYYMMDD_序號` |
| orders | array | TRUE | 訂單列表，最多 1000 筆 |

### orders 陣列欄位

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| order_id | string | TRUE | 訂單識別碼，最多 64 字 |
| action | string | TRUE | 僅接受 `COMPLETED` \| `CANCELLED` |

## Request Sample（JSON）

```json
{
  "request_id": "BATCH_20261003_001",
  "orders": [
    { "order_id": "ORD_20261001_00001", "action": "COMPLETED" },
    { "order_id": "ORD_20261001_00002", "action": "CANCELLED" }
  ]
}
```

# Response
HTTP Status: `200 OK`

## Response Sample（JSON）

```json
{
  "request_id": "BATCH_20261003_001",
  "accepted_count": 2,
  "submitted_at": "2026-10-03T10:00:00+08:00"
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| request_id | String | 發卡主機提供的批次識別碼，原樣回傳 |
| accepted_count | Integer | 本批次接收的訂單筆數 |
| submitted_at | Datetime | 批次接收時間（UTC+8 ISO 8601） |

### 邏輯說明
- 神坊收到請求後，建立 `finalize_batch_requests` 記錄，並逐筆建立 `finalize_batch_items`（初始狀態 `PENDING`），立即回傳 `200`
- 非同步 worker 處理各筆 item；每筆沿用原本的狀態轉換邏輯：
  - `action = COMPLETED`：所有對應券 `consumed → settled`，觸發代償流程
  - `action = CANCELLED`：`consumed` 券依是否到期轉為 `available` 或 `expired`，點數不返還
- 單筆驗證失敗（`ORDER_NOT_FOUND`、`ORDER_ALREADY_FINALIZED`）不中斷整批次，錯誤記錄於該 item 的 `error_code`

## 400 錯誤回傳（request-level）
1. `request_id` 未提供：`BATCH_REQUEST_ID_REQUIRED`
2. `orders` 未提供或為空陣列：`ORDERS_REQUIRED`
3. `orders` 超過 1000 筆：`BATCH_SIZE_EXCEEDED`
4. `orders` 內任一筆 `action` 值不合法：`INVALID_ACTION`
5. 相同 `request_id` 已存在：`BATCH_REQUEST_ALREADY_EXISTS`
