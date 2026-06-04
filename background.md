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
2. store: 品牌通路所底下的實體門店
3. campaign: 對應於品牌之下的產券邏輯
4. coupon: 基於 campaign 產出，所屬於用戶的 instance

## 本體概念：
Coupon 本質作為本體，不採取「刷卡代金」概念作為本體
- 不特別設計 balance 機制 (儲值於特定品牌下的儲值金)
- coupon 需支援：
  - 建立（清算可用點數後發券給用戶）
  - 成立訂單（用戶在商戶刷卡完成授權後，將券狀態改為處理中）
  - 完成訂單（待商戶向銀行請款後，將券狀態改為完成）
  - 取消訂單（商戶若向銀行申請刷退，將券狀態改為可使用，返回用戶券夾）
  - 過期

每一 brand 底下只會有一個「自動兌換」的 campaign
- 當用戶有同意「在此品牌刷卡時，自動以點數根據當前 campaign 兌換券」時
- 在對應品牌刷卡發生時，清算可折抵多少刷卡額

## 計算邏輯與概念
1. 已存在的 coupon 採 first-in-first-out -> 先到期先用
2. 若折抵的刷卡額扣抵後，還有刷卡額可以自動兌換之 campaign 扣抵，進行精算
3. 依照點數的數量，算出可再換多少張 coupon
4. 彙總回覆實際折抵刷卡額有多少

### 範例
campaign_rules:
- id = 'new_campaign'
- name = '滿100折21'
- unit_cash_amount = 100 (每刷 100 元可對應折抵一張)
- unit_point_amount = 20 (每一張券需要 20 點來換)
- unit_discount_amount = 21 (每一張券可折抵 21 元)

order:
- order_id = 'ord_01'
- cash_amount = 620

用戶已持有 coupon 共 1 張:
- coupon_id = 'coupon_01'
- campaign_id = 'old_campaign'
- unit_cash_amount = 400 (每刷 100 元可對應折抵一張)
- unit_point_amount = 100 (每一張券需要 20 點來換)
- unit_discount_amount = 120 (每一張券可折抵 21 元)

用戶持有點數:
- point_balance = 26

先計算已經有的部位：
cash_amount = 620
cash_amount - 400 = 220 (剩下可折抵的刷卡金為 220)

220 仍可再套用現行 campaign (id = 'new_campaign')
220 // 100 = 2，故可再以 2 張來折抵

而 point_balance(26) // unit_point_amount(20) = 1
因點數餘額只夠再折 1 張，只會換一張

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
1. brand_name
2. brand_logo
3. brand_category
4. brand_active_campaign_details

此流程由樹享券平台前台端串接品牌查詢 API。

## Flow 2: 選品牌
用戶選擇偏好 brand（特店） 例如：全家 / 7-11 or 康是美 / 屈臣氏 or 大全聯 / 頂好...etc
需檢查下述邏輯：
1. 用戶是否可以更換（商務規定上每月一次，應設定為環境參數）
2. 用戶選擇的品牌數量（商務規定上每人最多 3 個，應設定為環境參數）
3. 選擇的品牌是否有 active campaign 可選

此流程由樹享券平台前台端串接使用者設定 API。

## Flow 3: 瀏覽已選品牌
瀏覽用戶已選、且當前仍具備 active campaign 的品牌，需包含下列資料：
1. brand_name
2. brand_logo
3. brand_category
4. brand_active_campaign_details

若用戶尚未選擇任何品牌，或雖曾選擇品牌但目前沒有任何 brand 仍具備 active campaign，則以前台端空狀態呈現。

## Flow 4: 調閱異動紀錄
調閱用戶過往 1 年內的異動紀錄，包含異動時間與異動行為（首次啟用、暫停用券、重啟用券、更換品牌）
其中更換品牌需要包含「更換前有哪些」vs「更換後是哪些」

此流程由樹享券平台前台端串接異動紀錄 API。

## Flow 5: 刷卡
1. 由發卡主機刷卡交易 create_order (信用卡授權後執行)，並由神坊比對品牌與清算後發起用券
2. 由發卡主機回報商戶請款完成或取消交易，進行 finalize_order (後續待商戶請款才呼叫，非同步)

create_order 時，發卡主機需額外帶入用戶本次刷卡卡號後四碼，供後續前台端查詢訂單與呈現卡號辨識資訊。
