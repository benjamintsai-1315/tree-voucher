---
title: API Spec - get_finalize_batch_status
permalink: /api-specs/get-finalize-batch-status/
---

## Changelog

| Date | Summary |
| ---- | ------- |
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
  "submitted_at": "2026-10-03T10:00:00+08:00",
  "completed_at": null,
  "total_count": 2,
  "pending_count": 1,
  "success_count": 1,
  "failed_count": 0,
  "orders": [
    {
      "id": "ORD_20261001_00001",
      "action": "complete",
      "status": "SUCCESS",
      "finalized_at": "2026-10-03T10:00:05+08:00",
      "error_code": null
    },
    {
      "id": "ORD_20261001_00002",
      "action": "cancel",
      "status": "PENDING",
      "finalized_at": null,
      "error_code": null
    }
  ]
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| request_id | String | 批次識別碼 |
| status | String | 批次整體狀態，見下表 |
| submitted_at | Datetime | 批次接收時間（UTC+8 ISO 8601） |
| completed_at | Datetime \| null | 所有 item 處理完成時間（UTC+8 ISO 8601）；尚未完成時為 `null` |
| total_count | Integer | 批次內訂單總筆數 |
| pending_count | Integer | 尚未處理的筆數 |
| success_count | Integer | 成功處理的筆數 |
| failed_count | Integer | 處理失敗的筆數 |
| orders | Array | 各筆訂單的處理明細 |

### orders

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 訂單識別碼 |
| action | String | `complete` \| `cancel` |
| status | String | 單筆處理狀態，見下表 |
| finalized_at | Datetime \| null | 單筆處理成功時間（UTC+8 ISO 8601）；尚未完成或失敗時為 `null` |
| error_code | String \| null | 失敗原因代碼；成功或待處理時為 `null` |

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
| `INVALID_ACTION` | `action` 值不合法（非 `complete`/`cancel`） |
| `ORDER_NOT_FOUND` | `order_id` 不存在於神坊系統 |
| `ORDER_ALREADY_FINALIZED` | 訂單已完成最終化，不可重複執行 |

## 400 錯誤回傳（TYPE: MESSAGE）
1. 批次請求不存在：`BATCH_REQUEST_NOT_FOUND`
