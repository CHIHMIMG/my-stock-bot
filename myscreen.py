import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
DISCORD_WEBHOOK_URL = '你的Discord網址' 

def send_discord(msg):
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        return r.status_code
    except:
        return "Error"

def screen_stocks():
    print("🚀 啟動全台股雲端篩選機...")
    dl = DataLoader()
    
    try:
        stock_info = dl.taiwan_stock_info()
        # 篩選出長度為 4 的代碼（排除權證、存託憑證等，只留普通股）
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功載入 {len(all_stocks)} 檔股票，開始全數掃描...")
    except Exception as e:
        print(f"❌ 取得清單失敗: {e}")
        return

    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    hits = []
    
    # --- 這裡已經移除限制，會跑完全台股 ---
    for sid, name in all_stocks:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20:
                continue
            
            today = df.iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            vol_k = today['Volume'] / 1000
            
            # 你的條件：股價 > 5MA 且 成交量 > 1000張
            if today['close'] > ma5 and vol_k > 1000:
                res = f"🔥 {sid} {name}: {today['close']} (量:{int(vol_k)}張)"
                hits.append(res)
        except:
            continue
            
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    final_msg = f"📊 **全台股篩選報告 ({report_time})**\n"
    final_msg += "條件：股價 > 5MA 且 成交量 > 1000張\n"
    final_msg += "--------------------------------\n"
    
    if hits:
        # 如果符合的標的太多（超過 20 檔），分批發送或截斷以免 Discord 報錯
        msg_content = "\n".join(hits[:30]) # 先取前 30 檔最熱門的
        final_msg += msg_content
    else:
        final_msg += "今日全台股無符合條件之標的。"
    
    send_discord(final_msg)
    print("✅ 全台股掃描完成！")

if __name__ == "__main__":
    screen_stocks()
