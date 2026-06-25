---
title: API Spec - finalize_order
permalink: /api-specs/finalize-order/
---

> **⚠️ Deprecated：** 此規格已由 [`batch_finalize_orders`](API%20Spec%20-%20batch_finalize_orders.md) 取代，請勿使用本文件。

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-16 | Coupon 狀態改名：`processing` → `consumed`、`completed` → `settled` |
| 2026-06-16 | 改為批次接收（`orders` 陣列）、非同步處理；response 改回 `202 Accepted` 並回傳 `request_id`；移除原單筆同步回傳欄位 |
| 2026-06-15 | Endpoint 改為 `/bank/finalize_order`（原 `/coupon/finalize_order`），依呼叫端分類路徑 |

# API: finalize_order

## 功能說明
讓發卡主機在商戶請款完成或申請退刷後，批次呼叫此 API 通知神坊更新訂單狀態。神坊收到請求後立即回應 `202 Accepted`，實際狀態轉換以非同步方式執行。發卡主機可透過 `get_finalize_batch_status` 查詢各筆訂單的處理進度。


## 權限需求
- 認證：Authorization: ApiKey {{發卡主機_api_key}}
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
- 若相同 `request_id` 再次呼叫，神坊直接回傳該批次的接收資訊，不重複建立
- 此設計讓發卡主機在首次呼叫未收到回應時，可重送請求並確認是否已被接收


# Request
HTTP method: `POST`
Endpoint: `/bank/finalize_order`
Content-Type: `application/json`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{issuer_api_key}}` |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| request_id | string | TRUE | FALSE | ❎ | 最多 64 字；由發卡主機自行產生，用於冪等識別 |
| orders | array | TRUE | FALSE | ❎ | 至少 1 筆，最多 100 筆 |
| orders[].order_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| orders[].action | string | TRUE | FALSE | ❎ | 僅接受 `COMPLETED` \| `CANCELLED` |

## Request Sample（JSON）

```json
{
  "request_id": "BREQ_20261003_00001",
  "orders": [
    { "order_id": "ORD_20261001_00001", "action": "COMPLETED" },
    { "order_id": "ORD_20261001_00002", "action": "CANCELLED" }
  ]
}
```

# Response
HTTP Status: `202 Accepted`

## Response Sample（JSON）

```json
{
  "request_id": "BREQ_20261003_00001",
  "accepted_count": 2,
  "submitted_at": "2026-10-03T10:00:00+08:00"
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| request_id | String | 發卡主機提供的批次識別碼，原樣回傳 |
| accepted_count | Integer | 本批次接收的訂單筆數 |
| submitted_at | Datetime | 批次接收時間（UTC+8 ISO 8601）；若為重送相同 `request_id`，回傳原始接收時間 |

### 邏輯說明
- 神坊收到請求後，建立（或查找）`finalize_batch_requests` 記錄，並逐筆建立 `finalize_batch_items`（初始狀態 `PENDING`），立即回傳 `202`
- 非同步 worker 處理各筆 item；每筆沿用原本的狀態轉換邏輯：
  - `action = COMPLETED`：所有對應券 `consumed → settled`，觸發代償流程
  - `action = CANCELLED`：`consumed` 券依是否到期轉為 `available` 或 `expired`，點數不返還
- 單筆驗證失敗（`ORDER_NOT_FOUND`、`ORDER_ALREADY_FINALIZED`）不中斷整批次，錯誤記錄於該 item 的 `error_code`
- 重送相同 `request_id`：直接回傳原批次接收資訊，不重複建立或重跑

## 400 錯誤回傳（request-level）
1. `orders` 為空陣列：`ORDERS_REQUIRED`
2. `orders` 超過 100 筆：`TOO_MANY_ORDERS`
3. `request_id` 未提供：`BATCH_REQUEST_ID_REQUIRED`
