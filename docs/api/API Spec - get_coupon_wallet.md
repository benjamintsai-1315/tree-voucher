---
title: API Spec - get_coupon_wallet
permalink: /api-specs/get-coupon-wallet/
---

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-07-27 | 補註 `unsettled_coupon_count`：DB 內部中間態 `consuming`（`create_order` 清算過程中）比照 `consumed` 一併計入聚合，不對前端另外揭露 |
| 2026-07-23 | `available_coupon_count` 更名為 `unsettled_coupon_count`，避免欄位名稱與 `available` 狀態值混淆（此欄位實際聚合 `available` + `consumed`，語意為「尚未走完流程（尚未 settled/expired）的券」） |
| 2026-07-22 | 效能討論定案：(1) 移除 366 天時間限制，品牌清單改為回傳所有曾經產生 coupon 發行紀錄的品牌（不限時間）；(2) `available_coupon_count` 改為聚合 `available` + `consumed`（尚可用或使用中皆計入），不再僅計 `available` |
| 2026-07-21 | coupon 狀態 enum 統一改為小寫（`available` 等），與 DB 一致，API 不做大小寫轉換 |
| 2026-07-14 | 修正範圍錯誤：品牌清單改為回傳過去一年內（查詢當下 T-366 天，含）有 coupon 發行紀錄的所有品牌，不再限於「當前 rotation 曾選過」；`brands: []` 條件同步改為「過去一年內無任何品牌換券紀錄」。原範圍會導致換檔後仍有可用舊券的品牌從券夾消失，屬邏輯錯誤 |
| 2026-07-02 | 新增邊界檢查：來源 IP 須在白名單內；`API Key` 與 IP 白名單皆存於 Parameter Store |
| 2026-07-02 | 新增邊界檢查與 400 錯誤：會員須已啟用（`MEMBER_NOT_ACTIVATED`） |
| 2026-07-02 | `brands` 陣列內欄位移除 `brand_` prefix：`brand_id/brand_name/brand_logo` → `id/name/logo` |
| 2026-07-01 | `brand_id` 範例值改為 ULID 格式，並於 response items 補上 ULID 型別註記 |
| 2026-06-23 | 重新設計為品牌摘要 API；原券列表功能移至 `get_coupons` |

# API: get_coupon_wallet

## 功能說明
查詢用戶券夾的品牌摘要。回傳該用戶所有曾經產生 coupon 發行紀錄的品牌（不限時間），以及各品牌目前尚可用／使用中券（`available` + `consumed`）的張數，供前端呈現品牌卡片列表（券夾首頁）。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹配券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - `member_id` 必須存在於神坊系統中
  - 呼叫前會員必須已啟用（`members.is_activated = TRUE`）
  - 來源 IP 須在白名單內

> **注意：** `API Key` 與來源 IP 白名單皆存於 AWS Parameter Store。

## 使用情境
前台端帶入 `member_id`，取得用戶目前券夾的品牌卡片摘要。前端可由此進入各品牌的券列表（`get_coupons`）。

若使用者從未有任何品牌的換券紀錄，回傳 `brands: []`，不視為錯誤。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_coupon_wallet`
Content-Type: `application/json`

## Request Header（表格）

| Header | 說明 |
| ------ | ---- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）

| 欄位 | 類型 | 必填 | 可空 | 預設值 | 限制條件 |
| ---- | ---- | ---- | ---- | ------ | -------- |
| member_id | string | TRUE | FALSE | ❎ | UUID |

# Response
## Sample（JSON）

```json
{
  "brands": [
    {
      "id": "01HZY9VC0T9M4T6W8Y1Z3B5CGK",
      "name": "全家便利商店",
      "logo": "https://cdn.example.com/logos/familymart.png",
      "unsettled_coupon_count": 3
    },
    {
      "id": "01HZYAWD1V0N5V7X9Z2A4C6DHM",
      "name": "7-ELEVEN",
      "logo": "https://cdn.example.com/logos/711.png",
      "unsettled_coupon_count": 0
    }
  ]
}
```

## Response items

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brands | Array | 用戶所有曾經產生 coupon 發行紀錄的品牌列表（不限時間） |

### brands

| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| id | String | 品牌識別碼（ULID） |
| name | String | 品牌名稱 |
| logo | String | 品牌 logo 圖片 URL |
| unsettled_coupon_count | Integer | 該品牌目前狀態為 `available` 或 `consumed` 的券張數（尚可用或使用中皆計入；即尚未走完流程、未進入 `settled`/`expired` 終態的券） |

### 邏輯說明
- 回傳用戶**所有**曾經產生 coupon 發行紀錄的品牌，不限時間、不限於當前 rotation 或當前已選品牌清單；包含 `unsettled_coupon_count = 0` 的品牌（券已全部用完或尚未發券）
- 品牌入列條件：該品牌下存在任一 coupon（不限時間、不限狀態）
- `unsettled_coupon_count` 聚合 `status IN (available, consumed)` 的券張數（尚可用或使用中皆計入，不受時間窗限制）；DB 內部中間態 `consuming`（2026-07-27 起，`create_order` 清算過程中）比照 `consumed` 一併計入，不對前端另外揭露
- 若用戶從未有任何品牌的 coupon 發行紀錄，回傳 `brands: []`，不報錯
- 排序依 `brand_name ASC`

## 400 錯誤回傳（TYPE: MESSAGE）
1. `member_id` 不存在：`MEMBER_NOT_FOUND`
2. 會員未啟用：`MEMBER_NOT_ACTIVATED`
