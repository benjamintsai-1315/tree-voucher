---
title: API Spec - update_member_settings
permalink: /api-specs/update-member-settings/
---

> ⚠️ **[DEPRECATED]** 此規格已於 2026-06-25 拆分為兩支獨立 endpoint，請勿使用本文件。
>
> 請參考：
> - 品牌選擇：[update_member_selected_brands](API%20Spec%20-%20update_member_selected_brands.md)
> - 暫停／啟用自動兌換：[update_member_auto_redeem_settings](API%20Spec%20-%20update_member_auto_redeem_settings.md)

## Changelog

| Date | Summary |
| ---- | ------- |
| 2026-06-25 | **[DEPRECATED]** 拆分為 `update_member_selected_brands` 與 `update_member_auto_redeem_settings` 兩支獨立 endpoint |
| 2026-06-23 | `PAUSE` / `RESUME` 新增冪等說明：當前狀態已與目標一致時，直接回傳現況，不寫異動 log |
| 2026-06-18 | 移除 `RESUME` 的 `NO_ACTIVE_SELECTED_BRANDS` 限制 |
| 2026-06-16 | 由 `update_member_selected_brands` 更名為 `update_member_settings`；endpoint 改為 `/coupon/update_member_settings` |
| 2026-06-12 | 由 `update_user_selected_brands` 更名 |
