import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'
VOL_THRESHOLD = 6000  
VOL_RATIO = 1.5       

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=10)
    except:
        pass

def screen_stocks():
    print("🚀 開始準確版掃描...")
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    all_stocks = stock_info[stock_info['stock_id'].str.len() == 4]['stock_id'].tolist()
    
    hits = []
    for sid in all_stocks:
        try:
            # yfinance 數據抓取
            df = yf.download(f"{sid}.TW", period="90d", progress=False)
            if df.empty:
                df = yf.download(f"{sid}.TWO", period="90d", progress=False)
            
            if len(df) < 61: continue

            # 成交量校正：Yahoo 是「股」，所以要除以 1000 變成「張」
            today_vol = float(df['Volume'].iloc[-1]) / 1000
            yesterday_vol = float(df['Volume'].iloc[-2]) / 1000
            close_price = float(df['Close'].iloc[-1])

            # 均線計算 (含今日)
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # 條件審查
            cond1 = today_vol >= VOL_THRESHOLD
            cond2 = close_price >= ma5 and close_price >= ma10 and close_price >= ma20 and close_price >= ma60
            cond3 = today_vol >= (yesterday_vol * VOL_RATIO)

            if cond1 and cond2 and cond3:
                res = f"🌟 {sid}: {round(close_price, 2)} (量:{int(today_vol)}張, 增:{round(today_vol/yesterday_vol, 2)}倍)"
                hits.append(res)
                print(f"✅ 命中: {sid}")

        except:
            continue
    
    if hits:
        send_discord("\n".join(hits))
    else:
        send_discord("📊 今日掃描完成，無符合標的。")

if __name__ == "__main__":
    screen_stocks()
