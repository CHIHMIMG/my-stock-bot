import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime

# --- 已套入您的設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    """發送警報至 Discord 與 LINE"""
    try:
        # Discord 發送
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
        
        # LINE 發送
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
        payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        print(f"發送警報失敗: {e}")

def check_breakthrough():
    if not os.path.exists('targets.txt'):
        print("找不到 targets.txt，請確認檔案是否存在於根目錄。")
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    if not targets:
        print("監控清單目前為空。")
        return
        
    still_watching = set()
    print(f"⏰ 啟動【1分鐘級別】即時價監控: {datetime.now().strftime('%H:%M:%S')}")

    for sid in targets:
        try:
            clean_sid = sid.strip()
            
            # 1. 下載日線數據（用來找歷史爆量低點）
            # 下載最近 10 天日線
            df_day = yf.download(f"{clean_sid}.TW", period="10d", interval="1d", progress=False)
            market_type = "TWSE"
            if df_day.empty:
                df_day = yf.download(f"{clean_sid}.TWO", period="10d", interval="1d", progress=False)
                market_type = "OTC"

            if df_day.empty or len(df_day) < 5:
                still_watching.add(clean_sid)
                continue

            # 2. 下載「1分鐘線」數據（抓取盤中最即時價格）
            # 抓最近 1 天的 1m 數據，取最後一筆 Close 作為現價
            df_now = yf.download(f"{clean_sid}.{'TW' if market_type=='TWSE' else 'TWO'}", 
                                 period="1d", interval="1m", progress=False)
            
            if not df_now.empty:
                current_price = float(df_now['Close'].iloc[-1])
            else:
                current_price = float(df_day['Close'].iloc[-1]) # 備案用日線現價

            # --- 核心邏輯：找出昨日、前天或大前天的爆量低點 ---
            support_price = None
            found_date = ""
            # 從昨日(-2)往回找 3 天 (排除今天索引 -1)
            for i in range(2, 5): 
                vol_target = df_day['Volume'].iloc[-i]
                vol_prev = df_day['Volume'].iloc[-i-1]
                
                # 判定爆量門檻：1.5 倍
                if vol_target >= (vol_prev * 1.5):
                    support_price = float(df_day['Low'].iloc[-i])
                    found_date = df_day.index[-i].strftime('%m/%d')
                    break 
            
            # --- 判斷是否跌破 ---
            if support_price and current_price < support_price:
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market_type}:{clean_sid}"
                msg = (f"🚨 【極速監控】跌破爆量支撐：{clean_sid}\n"
                       f"💰 即時價 {current_price:.2f} < {found_date} 支撐 {support_price:.2f}\n"
                       f"📊 今日成交量：{int(df_day['Volume'].iloc[-1]/1000)}張\n"
                       f"🔗 線圖連結：{tv_url}")
                send_alert(msg)
                print(f"🚨 {clean_sid} 觸發警報！即時價 {current_price} 低於支撐。")
            else:
                still_watching.add(clean_sid)
                status = f"支撐({found_date}):{support_price}" if support_price else "無支撐位"
                print(f"✅ {clean_sid} 監控中 (現價:{current_price} | {status})")
                
        except Exception as e:
            print(f"❌ 處理 {sid} 時發生錯誤: {e}")
            still_watching.add(sid)
        
    # 將未觸發警報的股票寫回 targets.txt，已觸發的就自動移除
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
