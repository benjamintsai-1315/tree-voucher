---
title: API Spec - get_user_selected_brands
permalink: /api-specs/get-user-selected-brands/
---

# API: get_user_selected_brands
## 功能說明
讓樹享券平台前台端以 API Key 依 user_id 取得該用戶目前的已選品牌狀態，包含服務是否啟用，以及目前已選擇、且當前仍具備 active campaign 的品牌清單與對應 active campaign 詳情，供前端呈現已選品牌頁面。

## 權限需求
- 認證：Authorization: `ApiKey {{treecoupon_frontend_api_key}}`
- 邊界檢查：
  - API Key 須為樹享券平台前台端專屬授權，不接受其他呼叫方的 API Key
  - user_id 必須存在於小樹生活中
  - 僅可查詢該 user_id 目前已選且仍具備 active campaign 的 brands

## 使用情境
前台端帶入 user_id 取得該用戶目前的品牌設定狀態。若服務未暫停，前端可依 `auto_redeem_enabled` 判斷服務是否啟用；並以 `brands` 顯示目前已選擇、且當前仍有 active campaign 的品牌與對應兌換條件。

若使用者尚未選擇任何品牌，或雖曾選擇品牌但目前沒有任何 brand 仍具備 active campaign，皆回傳空陣列 `brands: []`，不視為錯誤。

# Request
HTTP method: `GET`
Endpoint: `/coupon/get_user_selected_brands?user_id={{user_id}}`
Content-Type: `application/json`
## Request Header（表格）
| Header | 說明 |
| ------ | --- |
| Authorization | ApiKey {{treecoupon_frontend_api_key}} |

## Request Parameters
（query）
| 欄位 | 類型 | 必填 | 可空(可省略) | 預設值 | 限制條件 | 
| ---- | ---- | ---- | ---- | ---- | ---- |
| user_id | string | TRUE | FALSE | ❎ | UUID |

# Response
## Sample（JSON）
```json
{
  "user_id": "USR_000123",
  "auto_redeem_enabled": true,
  "brands": [
    {
      "brand_id": "BRAND_711",
      "brand_name": "7-ELEVEN",
      "brand_logo": "https://cdn.example.com/logos/711.png",
      "brand_category": "便利商店",
      "active_campaign": {
        "campaign_id": "CPN_CAMP_002",
        "campaign_name": "滿150折30",
        "unit_cash_amount": 150,
        "unit_point_amount": 25,
        "unit_discount_amount": 30,
        "max_redeem_count": 2,
        "updated_at": "2026-10-01T09:00:00+08:00"
      },
      "created_at": "2026-08-01T00:00:00+08:00",
      "updated_at": "2026-10-01T09:00:00+08:00"
    },
    {
      "brand_id": "BRAND_FAMILYMART",
      "brand_name": "全家便利商店",
      "brand_logo": "https://cdn.example.com/logos/familymart.png",
      "brand_category": "便利商店",
      "active_campaign": {
        "campaign_id": "CPN_CAMP_001",
        "campaign_name": "滿100折21",
        "unit_cash_amount": 100,
        "unit_point_amount": 20,
        "unit_discount_amount": 21,
        "max_redeem_count": 3,
        "updated_at": "2026-10-01T09:00:00+08:00"
      },
      "created_at": "2026-09-01T00:00:00+08:00",
      "updated_at": "2026-10-01T09:00:00+08:00"
    }
  ]
}
```

## Response items
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| user_id | String | 神坊用戶識別碼 |
| auto_redeem_enabled | Boolean | 使用者自動兌換服務是否啟用；`false` 表示目前為暫停用券狀態 |
| brands | Array | 該用戶目前已選擇、且當前仍具備 active campaign 的品牌清單 |

### brands
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| brand_id | String | 品牌識別碼 |
| brand_name | String | 品牌名稱 |
| brand_logo | String | 品牌 logo 圖片 URL |
| brand_category | String | 品牌分類（例：便利商店、藥妝、超市） |
| active_campaign | Object | 該品牌當前有效的 campaign 規則 |
| created_at | String | 品牌建立時間（UTC+8 ISO 8601） |
| updated_at | String | 品牌資料最後更新時間（UTC+8 ISO 8601） |

### active_campaign
| 欄位 | 類型 | 說明 |
| ---- | ---- | ---- |
| campaign_id | String | Campaign 識別碼 |
| campaign_name | String | Campaign 名稱 |
| unit_cash_amount | Integer | 每消費滿 N 元可對應使用一張券 |
| unit_point_amount | Integer | 兌換一張券所需點數 |
| unit_discount_amount | Integer | 一張券可折抵的金額（元） |
| max_redeem_count | Integer | 單筆交易中，當前 active campaign 最多可使用幾張券 |
| updated_at | String | Campaign 最後更新時間（UTC+8 ISO 8601） |

### 邏輯說明

- 回傳欄位結構與 get_active_brands 保持一致，避免前台端處理兩套品牌資料格式
- `auto_redeem_enabled` 為使用者層級服務狀態；`PAUSE` 後為 `false`，`RESUME` 後為 `true`
- 僅回傳該用戶已選擇、且當前仍具備 active campaign 的品牌，不回傳未選擇的 active brands，也不回傳已無 active campaign 的已選品牌
- 排列順序以 brand_category 由小到大排序；若 brand_category 相同，則依 brand_id 由小到大排序
- 若使用者存在但尚未選擇任何品牌，回傳 brands: []，不報錯
- 若使用者曾選擇品牌，但目前所有已選品牌都已無 active campaign，回傳 brands: []，不報錯

### 400 錯誤回傳（TYPE: MESSAGE）
- API Key 非屬前台端授權：CALLER_NOT_AUTHORIZED
- user_id 不存在：USER_NOT_FOUND
