import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請務必填入你正確的 Webhook 網址
DISCORD_WEBHOOK_URL = '你的Discord網址' 

def send_discord(msg):
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        return r.status_code
    except:
        return "Error"

def screen_stocks():
    print("🚀 啟動【昨日 1.5 倍量 + 全均線】掃描...")
    dl = DataLoader()
    
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功載入 {len(all_stocks)} 檔股票...")
    except Exception as e:
        print(f"❌ 取得清單失敗: {e}")
        return

    # 抓取過去 100 天資料確保均線準確
    start_date = (datetime.datetime.now() - datetime.timedelta(days=100)).strftime('%Y-%m-%d')
    hits = []
    
    for sid, name in all_stocks:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            # 確保資料量足夠 (至少要比昨天多一天，並能算 60MA)
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
            
            # 成交量
            today_vol = today['Volume']
            yesterday_vol = yesterday['Volume']
            vol_k = today_vol / 1000

            # --- 三大核心條件 ---
            # 1. 成交量門檻：日成交量 > 6000 張
            cond1 = vol_k > 6000
            
            # 2. 站上所有均線：5, 10, 20, 60 MA
            cond2 = close > ma5 and close > ma10 and close > ma20 and close > ma60
            
            # 3. 量能增長：今日成交量 > 昨日成交量 * 1.5
            cond3 = today_vol > (yesterday_vol * 1.5) if yesterday_vol > 0 else False
            
            if cond1 and cond2 and cond3:
                times = round(today_vol / yesterday_vol, 1) if yesterday_vol > 0 else 0
                res = f"🌟 {sid} {name}: {close} (量:{int(vol_k)}張, 較昨日增:{times}倍)"
                hits.append(res)
        except:
            continue
            
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    header = f"📊 **【1.5 倍量轉強】全台股報告 ({report_time})**\n條件：1.量>6000張 / 2.站上所有均線 / 3.量>昨日1.5倍\n"
    header += "--------------------------------\n"
    
    if not hits:
        send_discord(header + "今日市場較冷，無符合標的。")
    else:
        # 分批發送
        for i in range(0, len(hits), 20):
            msg = header if i == 0 else ""
            msg += "\n".join(hits[i:i+20])
            send_discord(msg)
    
    print("✅ 掃描完成！")

if __name__ == "__main__":
    screen_stocks()
