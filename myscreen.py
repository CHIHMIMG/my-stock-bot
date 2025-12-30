import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請務必確認這裡貼上的是完整的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = '請在此貼入你的Webhook網址' 

def send_discord(msg):
    """將訊息推播至 Discord"""
    data = {"content": msg}
    try:
        # 雲端執行建議 timeout 設長一點
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=20)
        print(f"Discord 傳送狀態: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"Discord 傳送失敗: {e}")
        return "Error"

def screen_stocks():
    print("🚀 啟動雲端自動選股系統...")
    dl = DataLoader()
    
    try:
        # 取得台股清單
        stock_info = dl.taiwan_stock_info()
        # 過濾出 4 位數的個股
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功取得清單，共 {len(all_stocks)} 檔")
    except Exception as e:
        print(f"❌ 無法取得股票清單: {e}")
        return

    # 設定回測日期 (過去 40 天)
    start_date = (datetime.datetime.now() - datetime.timedelta(days=40)).strftime('%Y-%m-%d')
    hits = []
    
    # 開始掃描 (為了確保雲端穩定，建議先跑前 200 檔測試，成功後可刪除 [:200])
    print("🔎 正在篩選符合條件的標的...")
    for sid, name in all_stocks[:200]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20:
                continue
            
            today = df.iloc[-1]
            # 簡單條件：收盤價 > 5日均線 且 成交量 > 1000張
