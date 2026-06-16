---
title: 背景說明
permalink: /background/
---

# 一、背景說明
原規劃：「點數 + 金流整合支付（點加金）」 
因 法規限制 → 支付案暫緩 
改為推動新模式：「券加金」模式（樹享券 2.0）

# 二、樹享券 2.0 定義
## 核心概念：
使用者刷卡消費後
系統即時觸發：
- 使用者點數 → 購買神坊發行之「消費券」
  - 本質上與一般商品票券不同
  - 相對禮票券定性，在定性上更趨向消費代金
- 該券立即（或出帳時）用於折抵本次消費

## 名詞定義：
1. brand: 合作的品牌通路，也稱為特店
2. campaign: 對應於品牌之下的產券邏輯
3. coupon: 基於 campaign 產出，所屬於用戶的 instance

## 本體概念：
Coupon 本質作為本體，不採取「刷卡代金」概念作為本體
- 不特別設計 balance 機制 (儲值於特定品牌下的儲值金)
- coupon 需支援：
  - 建立（清算可用點數後發券給用戶）
  - 成立訂單（用戶在商戶刷卡完成授權後，將券狀態改為處理中）
  - 完成訂單（待商戶向銀行請款後，將券狀態改為完成）
  - 取消訂單（商戶若向銀行申請刷退，將券狀態改為可使用，返回用戶券夾）
  - 過期

每一 brand 底下同一時間只會有一個「自動兌換」的 campaign
- 當用戶有同意「在此品牌刷卡時，自動以點數根據當前 campaign 兌換券」時
- 在對應品牌刷卡發生時，清算可折抵多少刷卡額
- campaign 是否為 active，依當前時間是否落在其 `start_at` 與 `end_at` 之間判斷

## 計算邏輯與概念
1. 已存在的 coupon 採 first-in-first-out -> 先到期先用
2. 若折抵的刷卡額扣抵後，還有刷卡額可以自動兌換之 campaign 扣抵，進行精算
3. 依照點數的數量，算出可再換多少張 coupon
4. 彙總回覆實際折抵刷卡額有多少

補充規則：
- `max_redemptions_per_order` 限制的是「當次交易中，屬於當前 active campaign 的券最多可使用幾張」
- 若舊券本身就是當前 active campaign 產出的券，會先吃掉這個 quota
- 歷史 campaign 的舊券不吃這個 quota，仍照 FIFO 規則先用

### 範例
campaign_rules:
- id = 'new_campaign'
- name = '滿100折21'
- coupon_min_order_amount = 100 (每刷 100 元可對應折抵一張)
- coupon_redeem_points = 20 (每一張券需要 20 點來換)
- coupon_discount_amount = 21 (每一張券可折抵 21 元)
- max_redemptions_per_order = 3 (單筆交易中，當前 active campaign 最多可使用 3 張券)

order:
- order_id = 'ord_01'
- cash_amount = 620

用戶已持有 coupon 共 1 張:
- coupon_id = 'coupon_01'
- campaign_id = 'old_campaign'
- coupon_min_order_amount = 400 (每刷 100 元可對應折抵一張)
- coupon_redeem_points = 100 (每一張券需要 20 點來換)
- coupon_discount_amount = 120 (每一張券可折抵 21 元)

用戶持有點數:
- point_balance = 26

先計算已經有的部位：
cash_amount = 620
cash_amount - 400 = 220 (剩下可折抵的刷卡金為 220)

220 仍可再套用現行 campaign (id = 'new_campaign')
220 // 100 = 2，故可再以 2 張來折抵

而 point_balance(26) // coupon_redeem_points(20) = 1
campaign 可用 quota 為 3 張
因點數餘額只夠再折 1 張，故 min(2, 1, 3) = 1，只會換一張

因 `coupon_01` 屬於 `old_campaign`，不是當前 active campaign，所以不占用 `max_redemptions_per_order`

進行點數扣點 point_balance -= 20
進行 coupon 派送 (coupon_02, campaign_id = 'new_campaign')
discount_amount = 120(coupon_01.discount_amount) + 21(coupon_02.discount_amount) = 141

Response discount_amount = 141

### 帳務流程：
1. 用戶授權商戶刷卡 620 元
2. 神坊扣用戶點數 20 點
3. 商戶向銀行請款 620 元
4. 神坊確定核銷兩張券
5. 神坊代償 141 元給銀行
6. 用戶僅剩 479 元卡費要繳

# 三、合作方與角色
1. 票券發行單位：神坊（我們）
2. 發起交易方：發卡主機（銀行信用卡系統）
3. 刷卡場域：品牌通路
4. 使用者介面：樹享券平台前台端

# 四、資訊流程
## Flow 1: 品牌一覽
用戶可先看到所有品牌和對應當期自動兌換的規則
需包含下列資料：
1. max_selectable_brand_count
1. brand_name
2. brand_logo
3. brand_category
4. brand_active_campaign_details

此流程由樹享券平台前台端串接品牌查詢 API。

## Flow 2: 選品牌
用戶選擇偏好 brand（特店） 例如：全家 / 7-11 or 康是美 / 屈臣氏 or 大全聯 / 頂好...etc
需檢查下述邏輯：
1. 用戶是否已完成點數授權，且神坊系統可取得或驗證該授權結果
2. 用戶是否可以更換（商務規定上每月一次，應設定為環境參數）
3. 用戶選擇的品牌數量（商務規定上每人最多 3 個，應設定為環境參數）
4. 選擇的品牌是否有 active campaign 可選

此流程由樹享券平台前台端串接使用者設定 API。

## Flow 3: 瀏覽已選品牌
瀏覽用戶目前的品牌設定狀態，需包含：
1. max_selectable_brand_count
2. auto_redeem_enabled
3. last_changed_at
4. 已選、且當前仍具備 active campaign 的品牌清單

品牌清單需包含下列資料：
1. brand_name
2. brand_logo
3. brand_category
4. brand_active_campaign_details

若用戶尚未選擇任何品牌，或雖曾選擇品牌但目前沒有任何 brand 仍具備 active campaign，則以前台端空狀態呈現。

若用戶已暫停用券，仍可回傳符合條件的已選品牌，但以前台端狀態欄位顯示 `auto_redeem_enabled = false`。

`last_changed_at` 代表用戶品牌設定狀態最近一次異動時間，包含首次選牌、更換品牌、清空品牌、`PAUSE`、`RESUME` 與系統季度批次清空。

## Flow 4: 調閱異動紀錄
調閱用戶過往 1 年內的異動紀錄，包含異動時間與異動行為（首次啟用、暫停用券、重啟用券、更換品牌）
其中更換品牌需要包含「更換前有哪些」vs「更換後是哪些」

底層資料模型採 `brand_change_logs` 單表事件模型：
- 同一 `request_id` 代表同一次異動批次
- 初次選牌時可在同批寫入多筆 `INITIAL_SELECTION`
- 一般品牌更換時可在同批寫入多筆 `ADD_BRAND` / `REMOVE_BRAND`
- `PAUSE` / `RESUME` 為單筆事件，且 `brand_id = null`
- 系統季度批次清空時，寫入單筆 `SYSTEM_CLEAR_BRANDS`

此流程由樹享券平台前台端串接異動紀錄 API。

## Flow 4-1: 季度批次清空已選品牌
初期活動設計可能會在每一季度開始前，由系統全量清空用戶所選品牌。

規則如下：
1. 清空所有目標用戶的 selected brands
2. `auto_redeem_enabled` 保留原值，不強制改為 `false`
3. 為每位受影響用戶寫入 `SYSTEM_CLEAR_BRANDS`
4. 該事件時間會成為 `get_member_selected_brands.last_changed_at`

## Flow 5: 券夾
調閱用戶券夾列表，預設回全部券狀態，並可依品牌或券狀態篩選。

需包含下列資料：
1. coupon_id
2. coupon_status
3. brand_name
4. brand_logo
5. campaign_name
6. coupon_min_order_amount
7. coupon_redeem_points
8. coupon_discount_amount
9. max_redemptions_per_order
10. expired_at

此流程由樹享券平台前台端串接券夾查詢 API。

## Flow 6: 刷卡
1. 由發卡主機刷卡交易 create_order (信用卡授權後執行)，並由神坊比對品牌與清算後發起用券；response 僅回 `discount_amount`
2. 由發卡主機回報商戶請款完成或取消交易，進行 finalize_order (後續待商戶請款才呼叫，非同步)

create_order 時，發卡主機需額外帶入用戶本次刷卡卡號後四碼，供後續前台端查詢訂單與呈現卡號辨識資訊。
若需查詢訂單完整資訊、用券明細或事件歷程，另以 `order_id` 呼叫 `get_order`。

訂單底層資料模型包含：
- `order_logs`：保存訂單建立與最終化歷程
- `order_coupon_items`：保存訂單用券明細快照
