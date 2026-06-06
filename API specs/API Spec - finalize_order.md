---
title: API Spec - finalize_order
permalink: /api-specs/finalize-order/
---

# API: finalize_order

## 功能說明
讓發卡主機以 API Key 於商戶請款完成或取消交易後，依 `order_id` 對既有折抵訂單做最終化處理，更新訂單終態與對應 coupon 狀態。

## 權限需求
- 認證：Authorization: `ApiKey {{issuer_api_key}}`
- 邊界檢查：
  - API Key 須為發卡主機專屬授權，不接受前台端或其他呼叫方的 API Key
  - `order_id` 必須存在於神坊系統中
  - 僅 `PROCESSING` 狀態的訂單可執行 finalize

## 使用情境
發卡主機於商戶完成請款後，以 `finalize_result = COMPLETED` 呼叫此 API；若商戶後續取消交易，則以 `finalize_result = CANCELLED` 呼叫此 API。

若同一 `order_id` 已完成最終化，任何再次收到的 `finalize_order` 請求皆不重做狀態轉換，直接回 `ORDER_ALREADY_FINALIZED`。

# Request
HTTP method: `POST`
Endpoint: `/coupon/finalize_order`
Content-Type: `application/json`

## Request Header（表格）
| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{issuer_api_key}} |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| order_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| finalize_result | string | TRUE | FALSE | ❎ | 僅接受 `COMPLETED` \| `CANCELLED` |

# Response
## Sample（JSON）

```json
{
  "order_id": "ORD_20261001_00001",
  "order_status": "COMPLETED",
  "finalize_result": "COMPLETED",
  "finalized_at": "2026-10-03T10:00:00+08:00"
}
```

## Response items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| order_status | String | 訂單最終狀態：`COMPLETED` \| `CANCELLED` |
| finalize_result | String | 本次 finalize 請求結果：`COMPLETED` \| `CANCELLED` |
| finalized_at | String | 訂單最終化時間（UTC+8 ISO 8601） |

### 邏輯說明
- `finalize_result = COMPLETED`：本次訂單所有 `processing coupon` 轉為 `completed`
- `finalize_result = CANCELLED`：本次訂單所有 `processing coupon` 若在 finalize 當下尚未到期則轉回 `available`；若已到期則轉為 `expired`。點數不返還
- 同一 `order_id` 僅允許成功 finalize 一次；任何再次收到的 `finalize_order` 請求皆回 `ORDER_ALREADY_FINALIZED`
- 不區分再次收到的是相同結果或不同結果；已 `COMPLETED` 後收到 `CANCELLED`，或已 `CANCELLED` 後收到 `COMPLETED`，皆回 `ORDER_ALREADY_FINALIZED`
- 重複 `finalize_order` 不得再次改變訂單狀態、券狀態、點數或新增事件

## 400 錯誤回傳（TYPE: MESSAGE）
1. API Key 非發卡主機授權：`CALLER_NOT_AUTHORIZED`
2. `order_id` 不存在：`ORDER_NOT_FOUND`
3. 訂單已完成最終化：`ORDER_ALREADY_FINALIZED`
4. `finalize_result` 不合法：`INVALID_FINALIZE_RESULT`
