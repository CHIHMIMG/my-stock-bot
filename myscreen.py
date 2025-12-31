import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests
import time

# --- 設定區 ---
# 注意：請確保此處字串乾淨，建議手動刪除後重新貼上
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL' 
VOL_THRESHOLD = 6000 
VOL_RATIO = 1.5      

def send_discord(msg):
    data = {"content": msg}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print(f"✅ 成功發送至 Discord: {msg[:20]}...")
        else:
            print(f"❌ Discord 回傳錯誤碼: {response.status_code}, 內容: {response.text}")
    except Exception as e:
        print(f"❌ 發送失敗，網路異常: {e}")

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動掃描 (門檻: {VOL_THRESHOLD}張 / 倍率: {VOL_RATIO}倍)...")
    
    dl = DataLoader()
    # 如果有 Token 建議加上：dl.login(token="YOUR_TOKEN")
    
    try:
        stock_info = dl.taiwan_stock_info()
        # 只取 4 位數個股，排除認購權證
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"📊 正在檢查全台股 {len(all_stocks)} 檔標的...")
    except Exception as e:
        print(f"⚠️ 無法取得股票清單: {e}")
        return

    start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
    hits = []
    
    for idx, (sid, name) in enumerate(all_stocks):
        # 顯示進度，避免以為程式當掉
        if idx % 100 == 0:
            print(f"⏳ 已掃描 {idx}/{len(all_stocks)} 檔...")
            
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            
            if df is None or len(df) < 61:
                continue
            
            # 轉換資料格式確保計算正確
            df['close'] = df['close'].astype(float)
            df['Volume'] = df['Volume'].astype(float)
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 計算均線
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma10 = df['close'].rolling(10).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            
            close = today['close']
            vol_k = today['Volume'] / 1000
            y_vol = yesterday['Volume']

            # 核心條件
            cond1 = vol_k >= VOL_THRESHOLD
            cond2 = close >= ma5 and close >= ma10 and close >= ma20 and close >= ma60
            cond3 = today['Volume'] >= (y_vol * VOL_RATIO)
            
            if cond1 and cond2 and cond3:
                growth = round(today['Volume'] / y_vol, 2)
                res = f"🌟 {sid} {name}: {close} (量:{int(vol_k)}張, 增:{growth}倍)"
                hits.append(res)
                print(f"🔥 命中標的: {res}")
                
        except Exception as e:
            # 不要完全隱藏錯誤，至少印出來看看
            print(f"⚠️ {sid} 處理錯誤: {e}")
            continue
        
        # 稍微緩衝，避免被 API 鎖 IP
        time.sleep(0.1)

    # --- 發送結果 ---
    if not hits:
        send_discord(f"📊 **掃描報告 ({report_time})**\n目前無符合「量增且站上均線」之標的。")
    else:
        header = f"📊 **強勢動能名單 ({report_time})**\n條件：量 > {VOL_THRESHOLD}張 & 增幅 > {VOL_RATIO}倍\n"
        send_discord(header)
        # 分段發送
        for i in range(0, len(hits), 10):
            msg = "\n".join(hits[i:i + 10])
            send_discord(msg)

    print("✅ 任務完成！")

if __name__ == "__main__":
    screen_stocks()
