---
title: API Spec - finalize_order
permalink: /api-specs/finalize-order/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-15 | Endpoint 改為 `/bank/finalize_order`（原 `/coupon/finalize_order`），依呼叫端分類路徑 |

# API: finalize_order

## 功能說明
讓發卡主機在商戶請款完成或申請退刷後，呼叫此 API 通知神坊更新訂單狀態。請款完成時，神坊將對應券狀態由 `processing` 改為 `completed`，並執行代償；退刷時，券狀態退回 `available`，點數不返還。


## 權限需求
- 認證：Authorization: ApiKey {{發卡主機_api_key}} 
- 邊界檢查：
  - 此 API Key 須為發卡主機專屬授權 
  - order_id 必須存在於神坊系統中 
  - order_id 對應訂單的券狀態必須為 processing，否則不可執行   


## 使用情境
若同一 `order_id` 已完成最終化，任何再次收到的 `finalize_order` 請求皆不重做狀態轉換，直接回 `ORDER_ALREADY_FINALIZED`。
### 請款完成（completed）
- 商戶向銀行請款後，發卡主機通知神坊
- 神坊將該訂單所有 `processing` 券改為 `completed`
- 神坊執行代償流程
### 退刷（cancelled）
- 商戶向銀行申請刷退後，發卡主機通知神坊 
- 神坊將該訂單所有 `processing` 券改回 `available`
- 點數不返還；退回的券（含本次即時兌換產生者）成為後續可用的舊券 


# Request
HTTP method: `POST`
Endpoint: `/bank/finalize_order`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | `ApiKey {{issuer_api_key}}` |

## Request Parameters
（json）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| order_id | string | TRUE | FALSE | ❎ | 最多 64 字 |
| action | string | TRUE | FALSE | ❎ | 僅接受 `COMPLETED` \| `CANCELLED` |

# Response
## Sample（JSON）

```json
{
  "order_id": "ORD_20261001_00001",
  "action": "COMPLETED",
  "finalized_at": "2026-10-03T10:00:00+08:00"
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| order_id | String | 訂單識別碼 |
| action | String | 本次 finalize 請求內容：`COMPLETED` \| `CANCELLED` |
| finalized_at | Datetime | 訂單最終化時間（UTC+8 ISO 8601） |

### 邏輯說明
- `action = COMPLETED`：所有對應券 processing → completed，觸發神坊代償流程 
- `action = CANCELLED`：本次訂單所有 `processing coupon` 若在 finalize(cancelled) 當下尚未到期則轉回 `available`；若已到期則轉為 `expired`。點數不返還
- 同一 `order_id` 僅允許成功 finalize 一次；任何再次收到的 `finalize_order` 請求皆回 `ORDER_ALREADY_FINALIZED`

## 400 錯誤回傳（TYPE: MESSAGE）
1. 訂單編號不存在：`ORDER_NOT_FOUND`
2. 訂單券狀態非 processing（已完成或已退刷）：`ORDER_ALREADY_FINALIZED`
