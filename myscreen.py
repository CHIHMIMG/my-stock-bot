import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime
import time

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'
VOL_THRESHOLD = 6000  # 成交量大於 6000 張
VOL_RATIO = 1.5       # 量增 1.5 倍以上

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
    except:
        pass

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動全台股掃描... (日期: {report_time})")
    
    # 取得台股代碼清單
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    # 篩選 4 位數個股 (上市/上櫃)
    stock_list = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    
    hits = []
    
    # 開始逐檔掃描
    for sid, name in stock_list:
        try:
            # 抓取 10 天歷史，確保能算昨日量與今日量
            # auto_adjust=False 是關鍵，否則股價與成交量會因除權息而對不準
            df = yf.download(f"{sid}.TW", period="90d", progress=False, auto_adjust=False)
            if df.empty or len(df) < 2:
                df = yf.download(f"{sid}.TWO", period="90d", progress=False, auto_adjust=False)
            
            if df.empty or len(df) < 61: continue

            # 修正 Yahoo 多層標題索引問題
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 抓取成交量 (Yahoo 原始單位是「股」，必須除以 1000 變「張」)
            today_vol = float(df['Volume'].iloc[-1]) / 1000
            yesterday_vol = float(df['Volume'].iloc[-2]) / 1000
            close_price = float(df['Close'].iloc[-1])

            # 計算均線 (對齊軟體)
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # 核心條件
            cond1 = today_vol >= VOL_THRESHOLD
            cond2 = close_price >= max(ma5, ma10, ma20, ma60)
            cond3 = today_vol >= (yesterday_vol * VOL_RATIO)

            # --- 2337 旺宏 專用驗證 ---
            if sid == '2337':
                print(f"📍 驗證 2337: 量={int(today_vol)}張, 昨量={int(yesterday_vol)}張, 價={close_price}")

            if cond1 and cond2 and cond3:
                growth = round(today_vol / yesterday_vol, 2)
                res = f"🌟 {sid} {name}: {round(close_price, 2)} (量:{int(today_vol)}張, 增:{growth}倍)"
                hits.append(res)
                print(f"🔥 命中: {res}")

        except Exception:
            continue
            
    # 發送通知
    if hits:
        header = f"📊 **強勢標的名單 ({report_time})**\n條件:量>6000張 & 量增1.5倍 & 站上所有均線\n"
        send_discord(header)
        for i in range(0, len(hits), 10):
            send_discord("\n".join(hits[i:i + 10]))
    else:
        send_discord(f"📊 掃描完成 ({report_time})，今日無標的符合。")

if __name__ == "__main__":
    screen_stocks()
