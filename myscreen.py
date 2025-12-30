import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests
# --- 1. 設定區 ---
# 請務必確認這裡貼入的是你完整的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = '請在此貼入你的Webhook網址' 

def send_discord(msg):
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        return r.status_code
    except:
        return "Error"

def screen_stocks():
    print("🚀 啟動雲端自動選股系統...")
    dl = DataLoader()
    
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    except Exception as e:
        print(f"❌ 無法取得股票清單: {e}")
        return

    # 設定回測起始日期 (過去 45 天)
    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    hits = []
    
    # 掃描前 100 檔進行測試
    print("🔎 正在篩選符合條件的標的...")
    for sid, name in all_stocks[:100]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20: continue
            
            today = df.iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            vol_k = today['Volume'] / 1000
            
            if today['close'] > ma5 and vol_k > 1000:
                hits.append(f"🔥 {sid} {name}: {today['close']} (量:{int(vol_k)}張)")
        except:
            continue
            
    # 發送訊息
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    final_msg = f"📊 **台股雲端選股報告 ({now_str})**\n" + "\n".join(hits)
    send_discord(final_msg)
    print("✅ 任務執行完畢！")

if __name__ == "__main__":
    screen_stocks()
