---
title: API Spec - get_rotation_config
permalink: /api-specs/get-rotation-config/
---

# API: get_rotation_config

## 功能說明
讓樹享券平台前台端取得目前 active rotation（輪播檔期）的設定資訊，供前端顯示活動期間、品牌選擇上限及兌換條件的說明文字。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key

## 使用情境
前台端呼叫此 API 取得當前檔期資訊，包含活動開始/結束時間、用戶本檔期最多可選品牌數，以及前端用於顯示的單位消費金額與折抵點數說明。

> **注意：** `display_unit_cash_amount` 與 `display_unit_point_amount` 目前供前端呈現說明文字（例如：「每消費 100 元折抵 10 點」），不影響實際清算邏輯。實際清算依各品牌 campaign 的 `unit_cash_amount`、`unit_point_amount` 規則執行。未來後台有 campaign 建立介面時，這兩個值將作為新建 campaign 的 default value。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_rotation_config`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
此 API 無 request parameters。

# Response
## Sample（JSON）

```json
{
  "rotation_key": "2026Q1",
  "start_time": "2026-01-01T00:00:00+08:00",
  "end_time": "2026-03-31T23:59:59+08:00",
  "max_selectable_brand_count": 3,
  "display_unit_cash_amount": 100,
  "display_unit_point_amount": 10
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| rotation_key | String | 當前檔期識別碼，e.g. `2026Q1` |
| start_time | String | 檔期開始時間（UTC+8 ISO 8601） |
| end_time | String | 檔期結束時間（UTC+8 ISO 8601） |
| max_selectable_brand_count | Integer | 本檔期用戶最多可選擇的品牌數量 |
| display_unit_cash_amount | Integer | 單位消費金額（元）。目前供前端說明文字使用；未來將作為後台新建 campaign 的 default value |
| display_unit_point_amount | Integer | 單位折抵點數。目前供前端說明文字使用；未來將作為後台新建 campaign 的 default value |

# Error Handling

| HTTP Status | Error Code | 說明 |
| ----------- | ---------- | ---- |
| 400 | `NO_ACTIVE_ROTATION` | 目前無 active rotation（未到開始時間或已過結束時間） |
