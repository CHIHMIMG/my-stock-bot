import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 設定區 ---
DISCORD_WEBHOOK_URL = '你的Discord網址' 

def send_discord(msg):
    data = {"content": msg}
    try:
        # 增加 timeout 確保網路波動不會斷線
        requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
    except:
        pass

def screen_stocks():
    print("🚀 啟動【防字數限制版】掃描...")
    dl = DataLoader()
    
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    except:
        return

    # 抓取資料
    start_date = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime('%Y-%m-%d')
    hits = []
    
    for sid, name in all_stocks:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 61: continue
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            close = today['close']
            
            # 均線
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma10 = df['close'].rolling(10).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            
            today_vol = today['Volume']
            yesterday_vol = yesterday['Volume']
            vol_k = today_vol / 1000

            # 你的核心條件：1.量>6000 2.全均線 3.量增1.1倍
            cond1 = vol_k >= 6000
            cond2 = close >= ma5 and close >= ma10 and close >= ma20 and close >= ma60
            cond3 = today_vol >= (yesterday_vol * 1.1)
            
            if cond1 and cond2 and cond3:
                res = f"🌟 {sid} {name}: {close} (量:{int(vol_k)}張, 較昨日增:{round(today_vol/yesterday_vol, 1)}倍)"
                hits.append(res)
        except:
            continue
            
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if not hits:
        send_discord(f"📊 **掃描報告 ({report_time})**\n今日無符合標的。")
    else:
        # --- 核心修正：每 10 檔拆成一則訊息發送 ---
        for i in range(0, len(hits), 10):
            chunk = hits[i:i + 10]
            title = f"📊 **強勢動能名單 (第 {int(i/10)+1} 組)**\n"
            msg = title + "\n".join(chunk)
            send_discord(msg)
            print(f"✅ 已發送一組名單 (共 {len(chunk)} 檔)")
    
    print("✅ 全數掃描並發送完成！")

if __name__ == "__main__":
    screen_stocks()
