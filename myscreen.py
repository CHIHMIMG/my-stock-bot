import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請務必確認這裡貼入的是你完整的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = '貼上你的Discord網址' 

def send_discord(msg):
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        return r.status_code
    except:
        return "Error"

def screen_stocks():
    print("🚀 啟動【強勢爆量】選股機器人 (全台股掃描)...")
    dl = DataLoader()
    
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功載入 {len(all_stocks)} 檔股票，開始分析...")
    except Exception as e:
        print(f"❌ 取得清單失敗: {e}")
        return

    # 抓取過去 80 天資料以計算 60MA (季線)
    start_date = (datetime.datetime.now() - datetime.timedelta(days=80)).strftime('%Y-%m-%d')
    hits = []
    
    for sid, name in all_stocks:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 60: # 確保有足夠資料算季線
                continue
            
            # --- 價格與均線計算 ---
            today = df.iloc[-1]
            close = today['close']
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma10 = df['close'].rolling(10).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            
            # --- 成交量計算 ---
            today_vol = today['Volume']
            vol_k = today_vol / 1000
            # 計算過去五日平均成交量 (不含今天)
            ma5_vol = df['Volume'].iloc[-6:-1].mean()
            
            if ma5_vol == 0: continue
            
            # --- 核心三大條件篩選 ---
            # 1. 爆量 3 倍：當日成交量 > 五日均量 * 3
            cond1 = today_vol > (ma5_vol * 3)
            # 2. 站上
