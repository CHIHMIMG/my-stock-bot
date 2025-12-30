import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests
import os

# --- 1. 設定區 ---
# 請務必確認這串 Webhook 網址是完整的！
DISCORD_WEBHOOK_URL = '你的Discord網址' 

def send_discord(msg):
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=15)
        print(f"Discord 回傳狀態: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"Discord 發送失敗: {e}")
        return "Error"

def screen_stocks():
    print("🚀 啟動雲端選股器...")
    dl = DataLoader()
    
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功取得 {len(all_stocks)} 檔標的")
    except Exception as e:
        print(f"❌ 無法取得清單: {e}")
        return

    # 為了測試速度，我們只跑前 50 檔，成功收到通知後再改回全跑
    hits = []
    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    
    for sid, name in all_stocks[:50]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20: continue
            
            today = df.iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            if today['close'] > ma5:
                hits.append(f"✅ {sid} {name}: {today['close']}")
        except:
            continue
            
    msg = "📈 雲端測試報告：\n" + ("\n".join(hits) if hits else "目前測試範圍無符合標的")
    send_discord(msg)

if __name__ == "__main__":
    screen_stocks()
