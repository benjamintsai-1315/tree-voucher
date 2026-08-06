# docs/ 文件索引

## 目錄結構

| 路徑 | 內容 |
|---|---|
| `docs/api/` | API 規格文件（18 個 API spec） |
| `docs/changelogs/CHANGELOG.md` | 文件變更歷程 |
| `docs/樹配券2.0_PRD.md` | 核心產品需求文件（2026-07-13 由 repo root 移入；內容尚未跟上近期 API spec 變更，待後續整理） |
| `docs/reviews/` | spec-audit 復盤報告 |
| `docs/misc/` | 其他未歸類文件（如對外溝通用彙整文件） |

## 其他重要文件（位於 repo root）

| 檔案 | 內容 |
|---|---|
| `background.md` | 專案背景與業務邏輯說明 |
| `api_list.md` | API 範圍總覽清單 |
| `api-specs.md` | API spec 索引（對應 docs/api/ 下各檔案） |

## API spec 清單

### 前台（`/coupon/...`）

| API | 檔案 |
|---|---|
| `get_current_rotation` | `docs/api/API Spec - get_current_rotation.md` |
| `activate_member` | `docs/api/API Spec - activate_member.md` |
| `deactivate_member` | `docs/api/API Spec - deactivate_member.md` |
| `get_member_settings` | `docs/api/API Spec - get_member_settings.md` |
| `update_member_settings` | `docs/api/API Spec - update_member_settings.md` |
| `get_member_settings_change_logs` | `docs/api/API Spec - get_member_settings_change_logs.md` |
| `get_coupon_wallet` | `docs/api/API Spec - get_coupon_wallet.md` |
| `get_coupons` | `docs/api/API Spec - get_coupons.md` |
| `get_coupon_detail` | `docs/api/API Spec - get_coupon_detail.md` |
| `get_member_orders` | `docs/api/API Spec - get_member_orders.md` |
| ~~`get_order`~~ | `docs/api/legacy/API Spec - get_order.md`（⚠️ 已於 2026-07-08 廢除，前台不提供單筆訂單明細；改用 `get_member_orders`，發卡主機端用 `get_order`（發卡主機端）） |

### 發卡主機（`/bank/...`）

| API | 檔案 |
|---|---|
| `create_order` | `docs/api/API Spec - create_order.md` |
| `batch_finalize_orders` | `docs/api/API Spec - batch_finalize_orders.md` |
| `get_finalize_batch_status` | `docs/api/API Spec - get_finalize_batch_status.md` |
| `get_order` | `docs/api/API Spec - get_order.md`（2026-08-06 起，原名 `bank_get_order`） |
