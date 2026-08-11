---
title: API Spec - get_batch_finalize_result_file
permalink: /api-specs/get-batch-finalize-result-file/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-08-11 | 依銀行提供之最新規格文件訂正：Response Body 欄位改為 `line_no`／`order_id`／`action`／`status`／`error_type`（移除 `id`／`finalized_at`／`error_code`／`raw_data` 命名，改採與 `batch_finalize_orders` 內部 item 表一致的欄位名稱）；`error_type` 列表同步 `batch_finalize_orders.md` 本次訂正：`FILE_PARSE_ERROR` 拆回 `INVALID_JSON`／`INVALID_PAYLOAD`，移除 `INVALID_ACTION`（併入 `INVALID_PAYLOAD`） |
| 2026-08-11 | 新增 API，供發卡主機下載指定批次 finalize 請求的逐筆處理結果檔案；逐筆明細內容原包含於 `get_batch_finalize_status` inline `orders[]`（已於 2026-08-11 移除） |

# API: get_batch_finalize_result_file

## 功能說明
發卡主機以 `request_id` 取得指定批次 finalize 請求的逐筆處理結果檔案（CSV 或 JSON Lines），供批次筆數較多、不適合以單一 JSON response 承載明細時使用。結果檔案於批次狀態轉為 `completed` 後由背景程序產生並存放於 S3；呼叫本 API 時以 streaming 方式即時回傳檔案內容。


## 權限需求
- 認證：Authorization: ApiKey {{issuer_api_key}}
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權
  - 來源 IP 需在白名單內
    - note: API Key 與 IP 白名單皆存於 AWS Parameter Store
  - `request_id` 必須存在於神坊系統中


# Request
HTTP method: `GET`
Endpoint: `/bank/get_batch_finalize_result_file`

## Request Header

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{issuer_api_key}}` |

## Request Parameters（Query String）

| 欄位 | 類型 | 必填 | 說明 |
| ---- | ---- | ---- | ---- |
| request_id | string | TRUE | 批次請求識別碼 |
| format | string | FALSE | 回傳格式，enum `csv` \| `jsonline`，預設 `jsonline`（⚠️ 待確認：default 值與是否必填為建議值，執行時可再與發卡主機確認） |


# Response

> 本 API 回傳值非 JSON，而是以 streaming 方式回傳檔案內容。

## Response Headers

| Header | 值 |
| ------ | -- |
| Content-Type | `text/csv`（`format=csv`）或 `application/x-ndjson`（`format=jsonline`） |
| Content-Disposition | `attachment; filename="{request_id}.{csv\|jsonl}"` |

## Response Body

每一行（或 CSV 每一列）對應一筆訂單處理結果，欄位說明如下：

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| line_no | Integer | 原始 ndjson 檔案中的行號（1-based）；解析失敗的行亦保留行號，供發卡主機對照原始檔案確認 |
| order_id | String \| null | 訂單識別碼；該行原始內容解析失敗（無法取得 order_id）時為 `null` |
| action | String \| null | `complete` \| `cancel`；解析失敗時為 `null` |
| status | String | 單筆處理狀態，見下表 |
| error_type | String \| null | 失敗原因代碼；成功或待處理時為 `null` |

### Item Status Enum

| 狀態 | 說明 |
| ---- | ---- |
| `PENDING` | 尚未處理 |
| `SUCCESS` | 處理成功 |
| `FAILED` | 處理失敗，`error_type` 說明原因 |

### Item Error Type 說明

| error_type | 說明 |
| ---------- | ---- |
| `INVALID_JSON` | 該行 Json Line 無法解析 |
| `INVALID_PAYLOAD` | Payload 無法解析或欄位格式錯誤（缺 `order_id`／`action` 必要欄位、欄位長度超過上限，或 `action` 值不合法） |
| `DUPLICATE_ORDER_ID` | 同一批 `order_id` 重複；以第一筆格式合法的資料為有效項目，後續資料不執行結案 |
| `ORDER_NOT_FOUND` | 訂單不存在於票券系統 |
| `ORDER_ALREADY_FINALIZED` | 訂單已為終態，不可重複執行（`status: completed, cancelled`） |
| `ORDER_NOT_FINALIZABLE` | 訂單存在，但目前狀態不可結案（`status: pending`） |
| `ORDER_FAILED` | 訂單存在，但先前 `create_order` 失敗，無法執行結案（`status: error`） |

## Response Sample（JSON Lines）

```
{"line_no": 1, "order_id": "ORD_20261001_00001", "action": "complete", "status": "SUCCESS", "error_type": null}
{"line_no": 2, "order_id": "ORD_20261001_00002", "action": "cancel", "status": "PENDING", "error_type": null}
{"line_no": 3, "order_id": null, "action": null, "status": "FAILED", "error_type": "INVALID_JSON"}
```

## Response Sample（CSV）

```
line_no,order_id,action,status,error_type
1,ORD_20261001_00001,complete,SUCCESS,
2,ORD_20261001_00002,cancel,PENDING,
3,,,FAILED,INVALID_JSON
```

## 400 錯誤回傳（TYPE: MESSAGE）
1. 批次請求不存在：`BATCH_REQUEST_NOT_FOUND`
2. 結果檔案尚未就緒：`RESULT_FILE_NOT_READY`（⚠️ 待確認：是否允許 `processing` 中下載部分結果，目前預設不允許；批次尚未達到 `completed` 狀態時回傳此錯誤）
