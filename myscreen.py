import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請務必確認這裡貼入的是你完整的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = '在此貼入你的Discord網址' 

def send_discord(msg):
    """傳送訊息到 Discord"""
    data = {"content": msg}
    try:
        # 設定較長的 timeout 確保雲端連線穩定
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=20)
        print(f"Discord 傳送結果: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"Discord 傳送失敗: {e}")
        return "Error"

def screen_stocks():
    print("🚀 啟動雲端自動選股系統...")
    dl = DataLoader()
    
    try:
        # 抓取台股清單
        stock_info = dl.taiwan_stock_info()
        # 過濾出 4 位數的個股代碼
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功取得清單，共 {len(all_stocks)} 檔標的")
    except Exception as e:
        print(f"❌ 無法取得股票清單: {e}")
        return

    # 設定回測起始日期 (過去 45 天)
    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    hits = []
    
    # 開始掃描 (為了雲端穩定，我們先跑前 150 檔測試，成功後可刪除 [:150])
    print("🔎 正在篩選符合條件的標的...")
    for sid, name in all_stocks[:150]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20:
                continue
            
            today = df.iloc[-1]
            # 策略條件：股價 > 5日均線 且 成交量 > 1000張
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            vol_k = today['Volume'] / 1000
            
            if today['close'] > ma5 and vol_k > 1000:
                res = f"🔥 {sid} {name}: {today['close']} (量:{int(vol_k)}張)"
                hits.append(res)
                print(f"🎯 發現標的: {res}")
        except:
            continue
            
    # 組合訊息
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    final_msg = f"📊 **台股雲端選股報告 ({now_str})**\n"
    final_msg += "條件：股價 > 5MA 且 成交量 > 1000張\n"
    final_msg += "--------------------------------\n"
    final_msg += "\n".join(hits) if hits else "今日測試範圍內無符合條件之標的。"
    
    send_discord(final_msg)
    print("✅ 任務執行完畢！")

if __name__ == "__main__":
    screen_stocks()
