import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請務必確認這裡貼入的是完整的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = '請在這裡貼上你的網址' 

def send_discord(msg):
    """將結果發送到 Discord"""
    data = {"content": msg}
    try:
        # 雲端執行建議 timeout 設長一點
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        print(f"Discord 狀態碼: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"發送失敗: {e}")
        return "Error"

def screen_stocks():
    print("🚀 啟動台股雲端篩選機...")
    dl = DataLoader()
    
    try:
        # 取得台股清單並篩選 4 位數代碼
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功載入 {len(all_stocks)} 檔股票")
    except Exception as e:
        print(f"❌ 取得清單失敗: {e}")
        return

    # 設定回測日期
    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    hits = []
    
    # 開始篩選 (為了穩定，我們先跑前 100 檔進行測試)
    print("🔎 正在分析數據...")
    for sid, name in all_stocks[:100]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20:
                continue
            
            today = df.iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            vol_k = today['Volume'] / 1000
            
            # 條件：收盤價 > 5日均線 且 成交量 > 1000張
            if today['close'] > ma5 and vol_k > 1000:
                res = f"🔥 {sid} {name}: {today['close']} (量:{int(vol_k)}張)"
                hits.append(res)
                print(f"🎯 發現標的: {res}")
        except:
            continue
            
    # 組合訊息
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    final_msg = f"📊 **雲端選股報告 ({report_time})**\n"
    final_msg += "條件：股價 > 5MA 且 成交量 > 1000張\n"
    final_msg += "--------------------------------\n"
    final_msg += "\n".join(hits) if hits else "目前測試範圍內無符合標的。"
    
    send_discord(final_msg)
    print("✅ 任務已完成！")

if __name__ == "__main__":
    screen_stocks()
