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
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
        payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def check_breakthrough():
    if not os.path.exists('targets.txt'):
        print("找不到 targets.txt")
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    if not targets:
        print("監控清單目前為空。")
        return
        
    still_watching = set()
    print(f"⏰ 啟動【1分鐘級別】即時監控: {datetime.now().strftime('%H:%M:%S')}")

    for sid in targets:
        try:
            clean_sid = sid.strip()
            
            # 1. 下載 1 分鐘線抓即時價 (優先嘗試上市 .TW)
            df_now = yf.download(f"{clean_sid}.TW", period="1d", interval="1m", progress=False)
            market_type = "TWSE"
            if df_now.empty:
                df_now = yf.download(f"{clean_sid}.TWO", period="1d", interval="1m", progress=False)
                market_type = "OTC"
            
            if df_now.empty:
                still_watching.add(clean_sid)
                continue

            # 2. 下載日線找過去 3 天的支撐位
            df_day = yf.download(f"{clean_sid}.{'TW' if market_type=='TWSE' else 'TWO'}", 
                                 period="10d", interval="1d", progress=False)
            
            current_price = float(df_now['Close'].iloc[-1])
            
            # 3. 找出爆量支撐 (1.5倍)
            support_price = None
            found_date = ""
            for i in range(2, 5): 
                if df_day['Volume'].iloc[-i] >= (df_day['Volume'].iloc[-i-1] * 1.5):
                    support_price = float(df_day['Low'].iloc[-i])
                    found_date = df_day.index[-i].strftime('%m/%d')
                    break 
            
            # 4. 判斷跌破
            if support_price and current_price < support_price:
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market_type}:{clean_sid}"
                msg = (f"🚨 【極速監控】跌破支撐：{clean_sid}\n"
                       f"💰 即時價 {current_price:.2f} < {found_date} 支撐 {support_price:.2f}\n"
                       f"📊 今日量：{int(df_day['Volume'].iloc[-1]/1000)}張\n"
                       f"🔗 線圖：{tv_url}")
                send_alert(msg)
            else:
                still_watching.add(clean_sid)
                
        except:
            still_watching.add(sid)
        
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
