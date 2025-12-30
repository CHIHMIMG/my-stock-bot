import pandas as pd
from FinMind.data import DataLoader
import datetime
import requests

# --- 1. 設定區 ---
# 請在此貼入你完整的 Discord Webhook 網址
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL' 

def send_discord(msg):
    """推播結果到 Discord"""
    data = {"content": msg}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=30)
        print(f"Discord 狀態碼: {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"發送失敗: {e}")
        return "Error"

def screen_stocks():
    print("🚀 啟動台股雲端篩選系統...")
    dl = DataLoader()
    
    try:
        # 取得個股清單
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
        print(f"✅ 成功載入 {len(all_stocks)} 檔標的")
    except Exception as e:
        print(f"❌ 取得清單失敗: {e}")
        return

    # 設定回測日期
    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    hits = []
    
    # 篩選前 200 檔進行測試
    print("🔎 正在分析個股數據...")
    for sid, name in all_stocks[:200]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date=start_date)
            if df is None or len(df) < 20:
                continue
            
            today = df.iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            vol_k = today['Volume'] / 1000
            
            # 條件：股價高於5日線 且 成交量大於1000張
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
    final_msg += "\n".join(hits) if hits else "今日測試範圍內無符合標的。"
    
    send_discord(final_msg)
    print("✅ 任務已完成！")

if __name__ == "__main__":
    screen_stocks()
