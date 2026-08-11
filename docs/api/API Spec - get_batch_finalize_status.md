---
title: API Spec - get_batch_finalize_status
permalink: /api-specs/get-batch-finalize-status/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-11 | API 更名 `get_finalize_batch_status` → `get_batch_finalize_status`（對齊發卡主機提供之最新規格文件用語）；Response 精簡：移除 inline `orders[]` 逐筆明細（含對應 Item Status Enum、Item Error Code 說明），逐筆結果改由新 API `get_batch_finalize_result_file` 提供下載；`status` enum 由 3 態（大寫）擴充為 5 態（小寫）：`receiving`／`pending`／`processing`／`completed`／`error`；聚合統計欄位改包裝為 `result_statistics` 物件（原攤平於頂層）；重新啟用獨立結果檔案設計，但不否定 2026-07-30 決策：DB（`finalize_requests`／`finalize_request_order_items`）仍為 source of truth，僅將逐筆明細的對外呈現方式由 inline JSON 改為可下載／streaming 檔案；`result_statistics` 全程即時可見，非僅完成時才有值，與來源規格文件之呈現方式不同，以保留現行進度可視性 |
| 2026-08-06 | Item Error Code 補上 `DUPLICATE_ORDER_ID`（呼應 `batch_finalize_orders.md` 同日訂正：非同步階段對同批次重複 `order_id` 的判定，先前遺漏於本表） |
| 2026-07-30 | 呼應 batch_finalize_orders 同日變更：orders[] 新增 raw_data 欄位（原始內容解析失敗時揭露，id 為 null）；id／action 欄位在解析失敗時可為 null；Item Error Code 新增 FILE_PARSE_ERROR、ORDER_NOT_FINALIZABLE、ORDER_FAILED；ORDER_NOT_FOUND 定義收斂為單純查無此 order_id（不再涵蓋 error 訂單） |
| 2026-07-29 | 全系統時間精度盤點：`submitted_at`／`completed_at`／`finalized_at` 補註「毫秒精度」，Sample 補上 `.000` 精度 |
| 2026-07-21 | `orders[].action` 回傳值同步改為小寫 `complete`/`cancel`（原 `COMPLETED`/`CANCELLED`），與 `batch_finalize_orders` 本次調整對齊；Item Error Code 補上 `INVALID_ACTION`（該檢查已改列 `batch_finalize_orders` 非同步 item-level 錯誤） |
| 2026-06-23 | `items` 改名為 `orders`；`orders` 欄位說明獨立為子表格；移除 `order_` prefix |
| 2026-06-16 | 新增 API，供發卡主機查詢批次 finalize 請求的執行進度 |

# API: get_batch_finalize_status

## 功能說明
發卡主機呼叫 `batch_finalize_orders` 後取得 `request_id`，可透過此 API 查詢批次整體的處理進度與聚合統計。如需查詢批次內各筆訂單的處理明細，請改用 `get_batch_finalize_result_file`。


## 權限需求
- 認證：Authorization: ApiKey {{issuer_api_key}}
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - 來源 IP 需在白名單內
    - note: API Key 與 IP 白名單皆存於 AWS Parameter Store
  - `request_id` 必須存在於神坊系統中


# Request
HTTP method: `GET`
Endpoint: `/bank/get_batch_finalize_status`

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
  "status": "processing",
  "submitted_at": "2026-10-03T10:00:00.000+08:00",
  "completed_at": null,
  "result_statistics": {
    "total_count": 3,
    "pending_count": 1,
    "success_count": 1,
    "error_count": 1
  }
}
```

## Response Items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| request_id | String | 批次識別碼 |
| status | String | 批次整體狀態，見下表 |
| submitted_at | Datetime | 批次接收時間（UTC+8 ISO 8601，毫秒精度） |
| completed_at | Datetime \| null | 所有 item 處理完成時間（UTC+8 ISO 8601，毫秒精度）；尚未完成時為 `null` |
| result_statistics | Object | 批次聚合統計，見下表 |

### result_statistics

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| total_count | Integer | 批次內訂單總筆數 |
| pending_count | Integer | 尚未處理的筆數 |
| success_count | Integer | 成功處理的筆數 |
| error_count | Integer | 處理失敗的筆數 |

> `result_statistics` 於批次建立後即全程即時可見，非僅完成後才有值（實作上不會回傳 `null`）；此行為與來源規格文件（`result_statistics: null` 於處理中）不同，以保留進度可視性。

> `total_count` 包含所有 item（含解析失敗的行）；解析失敗的行建立當下即為 `error` 狀態並計入 `error_count`，不會出現在 `pending_count`。

### Batch Status Enum

| 狀態 | 說明 |
| ---- | ---- |
| `receiving` | 批次檔案接收中（`batch_finalize_orders` 同步階段，`finalize_requests` 初始狀態） |
| `pending` | 批次已建立，尚未開始處理任何 item |
| `processing` | 至少一筆 item 已開始處理，但尚未全部完成 |
| `completed` | 所有 item 皆已處理（含部分失敗） |
| `error` | 批次處理發生系統性錯誤（⚠️ 待確認：目前 `batch_finalize_orders.md` 的 Batch-level error 段落描述系統性失敗會 reset 回 `pending` 並發 alert、不會停留在對外可見的 `error` 狀態；此欄位對應的實際觸發條件與是否會被外部查詢到，需與 RD 進一步確認，本次先依來源規格文件納入 enum，語意待補） |

## 400 錯誤回傳（TYPE: MESSAGE）
1. 批次請求不存在：`BATCH_REQUEST_NOT_FOUND`
