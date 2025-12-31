import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests
import time

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL' 
VOL_THRESHOLD = 6000  # 維持你的要求：成交量必須大於 6000 張
VOL_RATIO = 1.5       # 修改要求：成交量為前一日之 1.5 倍

def send_discord(msg):
    data = {"content": msg}
    try:
        # 移除 try-except 中的 pass，增加錯誤偵測
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        if response.status_code != 204:
            print(f"❌ Discord 發送失敗，狀態碼: {response.status_code}。請檢查 Webhook 網址。")
    except Exception as e:
        print(f"❌ 網路連線錯誤: {e}")

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動掃描 (門檻: {VOL_THRESHOLD}張 / 倍率: {VOL_RATIO}倍)...")
    
    dl = DataLoader()
    # 如果你有 Token，建議加上：dl.login(token="你的Token")
    
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"📊 正在檢查全台股 {len(all_stocks)} 檔標的...")
    except Exception as e:
        send_discord(f"⚠️ **系統錯誤**：無法取得股票清單 ({e})")
        return

    start_date = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime('%Y-%m-%d')
    hits = []
    
    for sid, name in all_stocks:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            # 確保資料長度足夠計算 MA60
            if df is None or len(df) < 61: 
                continue
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            close = today['close']
            
            # 均線計算
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma10 = df['close'].rolling(10).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            
            today_vol = today['Volume']
            yesterday_vol = yesterday['Volume']
            vol_k = today_vol / 1000  # 換算為「張」

            # 核心篩選條件
            cond1 = vol_k >= VOL_THRESHOLD                   # 1. 成交量 > 6000 張
            cond2 = close >= ma5 and close >= ma10 and close >= ma20 and close >= ma60  # 2. 站上所有均線
            cond3 = today_vol >= (yesterday_vol * VOL_RATIO) # 3. 量增 1.5 倍以上
            
            if cond1 and cond2 and cond3:
                res = f"🌟 {sid} {name}: {close} (量:{int(vol_k)}張, 較昨日增:{round(today_vol/yesterday_vol, 2)}倍)"
                hits.append(res)
                print(f"🔥 符合條件: {sid} {name}")
                
        except:
            continue
            
    # --- 確保發送結果 ---
    if not hits:
        # 如果沒股票，依然發送通知，確保你知道程式運作正常
        send_discord(f"📊 **掃描報告 ({report_time})**\n今日成交量大於 6000 張且量增 1.5 倍之標的：**無**。")
    else:
        # 有標的則分段發送
        header = f"📊 **強勢動能名單 ({report_time})**\n條件：量 > {VOL_THRESHOLD}張 & 增幅 > {VOL_RATIO}倍\n"
        send_discord(header)
        
        for i in range(0, len(hits), 10):
            chunk = hits[i:i + 10]
            msg = "\n".join(chunk)
            send_discord(msg)
            time.sleep(1) 

    print("✅ 掃描與發送流程全數完成！")

if __name__ == "__main__":
    screen_stocks()
