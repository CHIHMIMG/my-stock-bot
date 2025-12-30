import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請確保這裡填入你正確的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = '你的Discord網址' 

dl = DataLoader()

def send_discord(msg):
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=15)
        return r.status_code
    except:
        return "Error"

def screen_stocks():
    print("🚀 啟動全台股篩選 (雲端模式)...")
    try:
        stock_info = dl.taiwan_stock_info()
        # 過濾出 4 位數的股票 (台股個股)
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    except Exception as e:
        print(f"❌ 無法取得清單: {e}")
        return

    start_date = (datetime.datetime.now() - datetime.timedelta(days=40)).strftime('%Y-%m-%d')
    hits = []
    
    # 掃描前 100 檔進行測試 (成功後可以把 [:100] 拿掉跑全台股)
    for sid, name in all_stocks[:100]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20: continue
            
            today = df.iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            vol_k = today['Volume'] / 1000
            
            # 條件：成交量 > 5000張 且 價格 > 5日線
            if vol_k > 5000 and today['close'] > ma5:
                res = f"🔥 {sid} {name}: {today['close']} (量:{int(vol_k)}張)"
                hits.append(res)
                print(f"🎯 發現標的: {res}")
        except:
            continue
            
    final_msg = "📈 今日選股報告：\n" + ("\n".join(hits) if hits else "今日無符合標的")
    send_discord(final_msg)
    print("✅ 掃描完成並已發送通知！")

if __name__ == "__main__":
    screen_stocks()
