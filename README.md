# 樹享券 2.0 (Tree Voucher 2.0)

數位點數折抵券系統的產品規格文件庫。本系統讓持卡人在信用卡消費時，自動將累積點數兌換為折抵券，並即時扣抵同筆消費金額（券加金模式）。

---

## 文件導覽

| 文件 | 說明 |
|------|------|
| [PRD](樹享券2.0_PRD.md) | 核心產品需求文件，涵蓋商業邏輯、狀態機與資訊流 |
| [背景說明](background.md) | 專案演進脈絡與「券加金」機制設計原由 |
| [資料庫 Schema](database-schema.md) | ER Diagram 與各資料表欄位定義 |
| [API 清單](api_list.md) | 全範圍 API 總表（前台、發卡主機、後台、批次） |
| [API 規格索引](api-specs.md) | 各 API 詳細規格連結 |
| [品牌識別機制](品牌識別機制.md) | 品牌匹配規則的兩種架構方案比較 |

---

## 系統概覽

```
持卡人消費
    │
    ▼
發卡主機 ──── create_order ────► 樹享券系統
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                    使用現有折抵券          從點數兌換新折抵券
                    (依到期日 FIFO)         (依活動規則計算)
                         │                     │
                         └──────────┬──────────┘
                                    │
                              回傳 discount_amount
                                    │
                         ◄── finalize_order ──── 發卡主機
                         (消費完成 / 取消)
```

---

## 核心概念

**輪播檔期 (Rotation)**
系統以「檔期」管理活動週期。每次檔期更換時，系統採用懶惰清除（lazy cleanup）機制，在使用者下次存取時自動更新其品牌選擇。

**折抵券狀態機**
```
AVAILABLE → CONSUMED → SETTLED
                     → AVAILABLE / EXPIRED (訂單取消時)
```

**點數扣除不退款原則**
`create_order` 時扣除的點數不因訂單取消而退還，僅折抵券狀態回復為 AVAILABLE。

---

## API 範圍

### 前台端（`/coupon/...`）

| API | Method | 說明 |
|-----|--------|------|
| `get_current_rotation` | GET | 取得當前檔期設定及有效活動品牌列表 |
| `activate_member` | POST | 會員同意啟用樹享券服務，更新授權狀態並寫入 log（原 `member_authorize`） |
| `deactivate_member` | POST | 會員主動解除服務，更新授權狀態並寫入 log（原 `member_unauthorize`） |
| `get_member_settings` | GET | 取得會員完整設定狀態（品牌選擇、自動兌換啟用狀態，觸發懶惰清除） |
| `update_member_selected_brands` | POST | 更新已選品牌清單（以完整清單覆蓋，後端計算 diff） |
| `update_member_auto_redeem_settings` | POST | 切換自動兌換服務狀態（暫停／啟用） |
| `get_member_settings_change_logs` | GET | 查詢設定異動紀錄（一年內） |
| `get_coupon_wallet` | GET | 查詢券夾品牌摘要（各品牌可用券張數） |
| `get_coupons` | GET | 查詢特定品牌下的券列表（支援狀態篩選） |
| `get_coupon_detail` | GET | 查詢單張券詳情（狀態、效期、兌換點數） |
| `get_member_orders` | GET | 查詢消費折抵紀錄 |
| ~~`get_order`~~ | GET | ⚠️ 已於 2026-07-08 廢除，前台不提供單筆訂單明細（改用 `get_member_orders`；發卡主機端用 `bank_get_order`） |

### 發卡主機端（`/bank/...`）

| API | Method | 說明 |
|-----|--------|------|
| `create_order` | POST | 建立折抵訂單（卡片授權後呼叫） |
| `batch_finalize_orders` | POST | 批次完成或取消訂單（非同步，202 回應） |
| `get_finalize_batch_status` | GET | 查詢批次 finalize 執行進度 |
| `bank_get_order` | GET | 查詢訂單狀態與折抵金額（僅回傳銀行端必要欄位） |

---

## 資料模型（主要資料表）

| 資料表 | 說明 |
|--------|------|
| `members` | 會員帳號與授權狀態 |
| `brands` | 合作品牌 |
| `campaigns` | 品牌折抵活動規則 |
| `rotations` | 輪播檔期設定 |
| `member_selected_brands` | 會員已選品牌（含檔期關聯） |
| `coupons` | 折抵券（含狀態、金額、到期日、campaign 規則快照） |
| `orders` | 折抵訂單 |
| `order_coupon_logs` | 訂單與折抵券的關聯日誌 |
| `member_settings_change_logs` | 設定異動事件日誌 |
| `member_authorization_logs` | 授權操作稽核紀錄 |

完整 ER Diagram 請見 [database-schema.md](database-schema.md)。

---

## 認證方式

- **前台 API：** `ApiKey {{treecoupon_frontend_api_key}}`
- **發卡主機 API：** `ApiKey {{issuer_api_key}}`

---

## 線上文件

本 repo 透過 GitHub Pages 發布靜態文件網站（Jekyll + Minima theme）。
