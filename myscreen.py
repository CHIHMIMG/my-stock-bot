import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL' # 請替換成你的 Webhook URL
VOL_THRESHOLD = 6000  # 成交量門檻：6000 張
VOL_RATIO = 1.5       # 量增倍率：1.5 倍

def send_discord(msg):
    """發送訊息至 Discord"""
    try:
        data = {"content": msg}
        res = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=15)
        if res.status_code == 204:
            print("✅ Discord 訊息發送成功")
        else:
            print(f"❌ Discord 發送失敗，狀態碼: {res.status_code}")
    except Exception as e:
        print(f"❌ 網路錯誤: {e}")

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動準確版掃描... 門檻: {VOL_THRESHOLD}張 / {VOL_RATIO}倍")
    
    # 1. 取得台股清單
    dl = DataLoader()
    try:
        stock_info = dl.taiwan_stock_info()
        # 僅取 4 位數代號，排除權證
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4]
        stock_list = all_stocks[['stock_id', 'stock_name']].values.tolist()
    except Exception as e:
        print(f"⚠️ 無法取得股票清單: {e}")
        return

    hits = []
    
    # 2. 開始掃描
    for sid, name in stock_list:
        try:
            # 優先嘗試上市 (.TW)，若無資料嘗試上櫃 (.TWO)
            df = yf.download(f"{sid}.TW", period="90d", progress=False)
            if df.empty or len(df) < 61:
                df = yf.download(f"{sid}.TWO", period="90d", progress=False)
            
            if df.empty or len(df) < 61:
                continue

            # --- 數據處理 ---
            # Yahoo 數據是「股」，必須除以 1000 變「張」
            today_vol = float(df['Volume'].iloc[-1]) / 1000
            yesterday_vol = float(df['Volume'].iloc[-2]) / 1000
            close_price = float(df['Close'].iloc[-1])

            # 計算均線 (MA)
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # --- 核心篩選條件 ---
            cond1 = today_vol >= VOL_THRESHOLD                   # 成交量 > 6000張
            cond2 = close_price >= max(ma5, ma10, ma20, ma60)    # 站上所有均線
            cond3 = today_vol >= (yesterday_vol * VOL_RATIO)     # 量增 1.5 倍以上

            # 特定追蹤：若掃描到 2337, 2377 則印出數值
            if sid in ['2337', '2377']:
                print(f"📍 檢查 {sid}: 價格 {round(close_price,1)}, 量 {int(today_vol)}張, 均線狀況={'符合' if cond2 else '未站上'}")

            if cond1 and cond2 and cond3:
                growth = round(today_vol / yesterday_vol, 2)
                res = f"🌟 **{sid} {name}**: {round(close_price, 2)} (量:{int(today_vol)}張, 較昨日增:{growth}倍)"
                hits.append(res)
                print(f"🔥 命中: {res}")

        except Exception:
            continue
            
    # 3. 發送報告
    if not hits:
        send_discord(f"📊 **掃描報告 ({report_time})**\n目前無符合「量 > 6000張 & 增幅 > 1.5倍 & 站上所有均線」之標的。")
    else:
        header = f"📊 **強勢動能名單 ({report_time})**\n"
        send_discord(header)
        # 分段發送，避免 Discord 字數限制
        for i in range(0, len(hits), 10):
            msg = "\n".join(hits[i:i + 10])
            send_discord(msg)

    print("✅ 全數掃描完成！")

if __name__ == "__main__":
    screen_stocks()
