---
title: API Spec - get_finalize_batch_status
permalink: /api-specs/get-finalize-batch-status/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-06 | Item Error Code 補上 `DUPLICATE_ORDER_ID`（呼應 `batch_finalize_orders.md` 同日訂正：非同步階段對同批次重複 `order_id` 的判定，先前遺漏於本表） |
| 2026-07-30 | 呼應 batch_finalize_orders 同日變更：orders[] 新增 raw_data 欄位（原始內容解析失敗時揭露，id 為 null）；id／action 欄位在解析失敗時可為 null；Item Error Code 新增 FILE_PARSE_ERROR、ORDER_NOT_FINALIZABLE、ORDER_FAILED；ORDER_NOT_FOUND 定義收斂為單純查無此 order_id（不再涵蓋 error 訂單） |
| 2026-07-29 | 全系統時間精度盤點：`submitted_at`／`completed_at`／`finalized_at` 補註「毫秒精度」，Sample 補上 `.000` 精度 |
| 2026-07-21 | `orders[].action` 回傳值同步改為小寫 `complete`/`cancel`（原 `COMPLETED`/`CANCELLED`），與 `batch_finalize_orders` 本次調整對齊；Item Error Code 補上 `INVALID_ACTION`（該檢查已改列 `batch_finalize_orders` 非同步 item-level 錯誤） |
| 2026-06-23 | `items` 改名為 `orders`；`orders` 欄位說明獨立為子表格；移除 `order_` prefix |
| 2026-06-16 | 新增 API，供發卡主機查詢批次 finalize 請求的執行進度 |

# API: get_finalize_batch_status

## 功能說明
發卡主機呼叫 `finalize_order` 後取得 `request_id`，可透過此 API 查詢各筆訂單的非同步處理進度。


## 權限需求
- 認證：Authorization: ApiKey {{發卡主機_api_key}}
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - `request_id` 必須存在於神坊系統中


# Request
HTTP method: `GET`
Endpoint: `/bank/get_finalize_batch_status`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{issuer_api_key}}` |

## Request Parameters（Query String）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| request_id | string | TRUE | 批次請求識別碼（由發卡主機提供） |


# Response
## Response Sample（JSON）

```json
{
  "request_id": "BREQ_20261003_00001",
  "status": "PROCESSING",
  "submitted_at": "2026-10-03T10:00:00.000+08:00",
  "completed_at": null,
  "total_count": 3,
  "pending_count": 1,
  "success_count": 1,
  "failed_count": 1,
  "orders": [
    {
      "id": "ORD_20261001_00001",
      "action": "complete",
      "status": "SUCCESS",
      "finalized_at": "2026-10-03T10:00:05.000+08:00",
      "error_code": null,
      "raw_data": null
    },
    {
      "id": "ORD_20261001_00002",
      "action": "cancel",
      "status": "PENDING",
      "finalized_at": null,
      "error_code": null,
      "raw_data": null
    },
    {
      "id": null,
      "action": null,
      "status": "FAILED",
      "finalized_at": null,
      "error_code": "FILE_PARSE_ERROR",
      "raw_data": "{\"order_id\": \"ORD_20261001_00003\", \"action\": }"
    }
  ]
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| request_id | String | 批次識別碼 |
| status | String | 批次整體狀態，見下表 |
| submitted_at | Datetime | 批次接收時間（UTC+8 ISO 8601，毫秒精度） |
| completed_at | Datetime \| null | 所有 item 處理完成時間（UTC+8 ISO 8601，毫秒精度）；尚未完成時為 `null` |
| total_count | Integer | 批次內訂單總筆數 |
| pending_count | Integer | 尚未處理的筆數 |
| success_count | Integer | 成功處理的筆數 |
| failed_count | Integer | 處理失敗的筆數 |
| orders | Array | 各筆訂單的處理明細 |

### orders

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String \| null | 訂單識別碼；該行原始內容解析失敗（無法取得 order_id）時為 `null` |
| action | String \| null | `complete` \| `cancel`；解析失敗時為 `null` |
| status | String | 單筆處理狀態，見下表 |
| finalized_at | Datetime \| null | 單筆處理成功時間（UTC+8 ISO 8601，毫秒精度）；尚未完成或失敗時為 `null` |
| error_code | String \| null | 失敗原因代碼；成功或待處理時為 `null` |
| raw_data | String \| null | 該行原始內容；僅在 `id` 為 `null`（解析失敗）時有值，其餘為 `null` |

> `total_count` 包含所有 item（含解析失敗的行）；解析失敗的行建立當下即為 `FAILED` 狀態並計入 `failed_count`，不會出現在 `pending_count`。

### Batch Status Enum

| 狀態 | 說明 |
| ---- | ---- |
| `PENDING` | 批次剛建立，尚未開始處理任何 item |
| `PROCESSING` | 至少一筆 item 已開始處理，但尚未全部完成 |
| `COMPLETED` | 所有 item 皆已處理（含部分失敗） |

### Item Status Enum

| 狀態 | 說明 |
| ---- | ---- |
| `PENDING` | 尚未處理 |
| `SUCCESS` | 處理成功，`finalized_at` 有值 |
| `FAILED` | 處理失敗，`error_code` 說明原因 |

### Item Error Code 說明

| error_code | 說明 |
| ---------- | ---- |
| `FILE_PARSE_ERROR` | 該行原始內容無法解析（非合法 JSON、缺 `order_id`／`action` 必要欄位，或欄位長度超過上限） |
| `DUPLICATE_ORDER_ID` | 同批次內 `order_id` 重複；以第一筆格式合法的資料為有效項目，後續資料不執行結案 |
| `INVALID_ACTION` | `action` 值不合法（非 `complete`/`cancel`） |
| `ORDER_NOT_FOUND` | `order_id` 不存在於神坊系統 |
| `ORDER_NOT_FINALIZABLE` | 訂單存在，但 `order.status = pending`（清算尚未完成，非唯一可終結狀態） |
| `ORDER_ALREADY_FINALIZED` | 訂單已完成最終化，不可重複執行 |
| `ORDER_FAILED` | 訂單存在，但 `order.status = error`（清算失敗，不可終結） |

## 400 錯誤回傳（TYPE: MESSAGE）
1. 批次請求不存在：`BATCH_REQUEST_NOT_FOUND`
