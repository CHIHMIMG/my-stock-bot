import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime
import requests
import time

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL' 
VOL_THRESHOLD = 6000  # 成交量大於 6000 張
VOL_RATIO = 1.5       # 量增 1.5 倍

def send_discord(msg):
    data = {"content": msg}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
    except:
        pass

def screen_stocks():
    print(f"🚀 啟動即時掃描 (目標: 2337, 2377 等全台股)...")
    
    # 1. 取得股票清單 (從 FinMind 拿清單比較快)
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    all_stocks = stock_info[stock_info['stock_id'].str.len() == 4]['stock_id'].tolist()
    
    hits = []
    total = len(all_stocks)

    for idx, sid in enumerate(all_stocks):
        try:
            # 2. 從 yfinance 抓取即時 + 歷史數據 (Yahoo 數據對台灣市場非常準確)
            # 格式需為 'XXXX.TW' (上市) 或 'XXXX.TWO' (上櫃)
            ticker_id = f"{sid}.TW"
            ticker = yf.Ticker(ticker_id)
            df = ticker.history(period="90d") # 抓 90 天確保足夠算 MA60
            
            if len(df) < 60:
                continue

            # 3. 數據定義 (Yahoo 的 Volume 單位是「股」，必須除以 1000)
            today_vol = df['Volume'].iloc[-1] / 1000
            yesterday_vol = df['Volume'].iloc[-2] / 1000
            close_price = df['Close'].iloc[-1]

            # 4. 計算均線 (與看盤軟體同步)
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # 核心篩選條件
            cond1 = today_vol >= VOL_THRESHOLD                   # 1. 成交量 > 6000張
            cond2 = close_price >= max(ma5, ma10, ma20, ma60)    # 2. 站在所有均線上
            cond3 = today_vol >= (yesterday_vol * VOL_RATIO)     # 3. 量增 1.5 倍以上

            # 除錯追蹤：如果是 2337 或 2377，強制印出數值核對
            if sid in ['2337', '2377']:
                print(f"🔍 檢查 {sid}: 價格={round(close_price,2)}, 量={int(today_vol)}張, 昨量={int(yesterday_vol)}張, 均線狀況={'符合' if cond2 else '未站上'}")

            if cond1 and cond2 and cond3:
                growth = round(today_vol / yesterday_vol, 2)
                res = f"🌟 {sid}: {round(close_price, 2)} (量:{int(today_vol)}張, 較昨日增:{growth}倍)"
                hits.append(res)
                print(f"🔥 命中標的: {res}")

        except Exception as e:
            continue
            
        # 顯示掃描進度
        if idx % 100 == 0:
            print(f"⏳ 進度: {idx}/{total}")

    # --- 發送結果 ---
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    if not hits:
        send_discord(f"📊 **掃描報告 ({report_time})**\n目前無符合「量 > 6000張 & 量增1.5倍 & 站上所有均線」之標的。")
    else:
        header = f"📊 **強勢動能名單 ({report_time})**\n"
        send_discord(header)
        for i in range(0, len(hits), 10):
            send_discord("\n".join(hits[i:i + 10]))

    print("✅ 掃描與發送流程完成！")

if __name__ == "__main__":
    screen_stocks()
