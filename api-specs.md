---
title: API 規格
permalink: /api-specs/
---

# 樹享券 2.0 API 規格

這裡集中列出目前已整理完成的 API spec，方便從同一頁面往下鑽。

## 樹享券平台前台端

- [get_current_rotation]({{ '/api-specs/get-current-rotation/' | relative_url }})
- [get_coupon_wallet]({{ '/api-specs/get-coupon-wallet/' | relative_url }})
- [get_coupons]({{ '/api-specs/get-coupons/' | relative_url }})
- [get_coupon_detail]({{ '/api-specs/get-coupon-detail/' | relative_url }})
- [get_member_settings]({{ '/api-specs/get-member-settings/' | relative_url }})
- [update_member_selected_brands]({{ '/api-specs/update-member-selected-brands/' | relative_url }})
- [update_member_auto_redeem_settings]({{ '/api-specs/update-member-auto-redeem-settings/' | relative_url }})
- [get_member_settings_change_logs]({{ '/api-specs/get-member-settings-change-logs/' | relative_url }})
- [get_member_orders]({{ '/api-specs/get-member-orders/' | relative_url }})
- ~~[get_order]({{ '/api-specs/get-order/' | relative_url }})~~ ⚠️ 已於 2026-07-08 廢除（前台改用 get_member_orders，發卡主機端用 bank_get_order）
- [activate_member]({{ '/api-specs/activate-member/' | relative_url }})
- [deactivate_member]({{ '/api-specs/deactivate-member/' | relative_url }})

## 發卡主機端

- [create_order]({{ '/api-specs/create-order/' | relative_url }})
- [batch_finalize_orders]({{ '/api-specs/batch-finalize-orders/' | relative_url }})
- [bank_get_order]({{ '/api-specs/bank-get-order/' | relative_url }})
