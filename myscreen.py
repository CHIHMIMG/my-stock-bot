import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime
import time

# --- 設定區 ---
# 這裡填入你的 Discord Webhook URL
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'
VOL_THRESHOLD = 6000  # 成交量大於 6000 張
VOL_RATIO = 2.0       # 量增 2 倍以上

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=20)
    except:
        pass

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動全台股掃描 (2倍量增模式)... (日期: {report_time})")
    
    # 取得台股代碼清單
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    stock_list = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    
    hits = []
    
    # 開始逐檔掃描
    for sid, name in stock_list:
        try:
            # 抓取數據
            df = yf.download(f"{sid}.TW", period="90d", progress=False, auto_adjust=False)
            if df.empty or len(df) < 61:
                df = yf.download(f"{sid}.TWO", period="90d", progress=False, auto_adjust=False)
            
            if df.empty or len(df) < 61: continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 抓取成交量與價格
            today_vol = float(df['Volume'].iloc[-1]) / 1000
            yesterday_vol = float(df['Volume'].iloc[-2]) / 1000
            close_price = float(df['Close'].iloc[-1])
            yesterday_close = float(df['Close'].iloc[-2])

            # 計算均線
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # 核心條件判斷
            cond_vol = today_vol >= VOL_THRESHOLD
            cond_ma = close_price >= max(ma5, ma10, ma20, ma60)
            cond_ratio = today_vol >= (yesterday_vol * VOL_RATIO)

            if cond_vol and cond_ma and cond_ratio:
                # 漲跌判斷顏色 (紅漲綠跌)
                price_diff = close_price - yesterday_close
                p_percent = (price_diff / yesterday_close) * 100
                icon = "🔴" if price_diff > 0 else "🟢" if price_diff < 0 else "🟡"
                
                growth = round(today_vol / yesterday_vol, 2)
                res = f"{icon} **{sid} {name}**: `{round(close_price, 2)}` ({p_percent:+.2f}%) | 量:{int(today_vol)}張 (爆發:{growth}倍)"
                hits.append(res)
                print(f"🔥 命中: {sid} {name}")

        except:
            continue
            
    # 發送通知
    if hits:
        header = f"📊 **【強勢標的：2.0倍量增專案】**\n篩選：量>6000張 & 增幅>2.0x & 站上全均線\n時間：{report_time}\n"
        send_discord(header)
        for i in range(0, len(hits), 10):
            send_discord("\n".join(hits[i:i + 10]))
    else:
        send_discord(f"📊 掃描完成 ({report_time})，今日無符合 2.0 倍量增標的。")

if __name__ == "__main__":
    screen_stocks()
