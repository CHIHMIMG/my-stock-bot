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
                print(f"❌ 無法取得 {clean_sid} 的即時數據")
                still_watching.add(clean_sid)
                continue

            # 2. 下載日線找支撐
            df_day = yf.download(f"{clean_sid}.{'TW' if market_type=='TWSE' else 'TWO'}", 
                                 period="10d", interval="1d", progress=False)
            
            current_price = float(df_now['Close'].iloc[-1])
            
            # 3. 找出過去 3 天爆量支撐 (1.5倍)
            support_price = None
            found_date = ""
            # 從昨日(-2)往回找
            for i in range(2, 5): 
                if df_day['Volume'].iloc[-i] >= (df_day['Volume'].iloc[-i-1] * 1.5):
                    support_price = float(df_day['Low'].iloc[-i])
                    found_date = df_day.index[-i].strftime('%m/%d')
                    break 
            
            # 4. 判斷跌破
            if support_price and current_price < support_price:
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market_type}:{clean_sid}"
                msg = (f"🚨 【盤中即時】跌破支撐：{clean_sid}\n"
                       f"💰 即時價 {current_price:.2f} < {found_date} 支撐 {support_price:.2f}\n"
                       f"📊 今日成交量：{int(df_day['Volume'].iloc[-1]/1000)}張\n"
                       f"🔗 線圖：{tv_url}")
                send_alert(msg)
                print(f"🚨 {clean_sid} 觸發！價格: {current_price}")
            else:
                still_watching.add(clean_sid)
                status = f"支撐({found_date}):{support_price}" if support_price else "未找到爆量日"
                print(f"✅ {clean_sid} 監控中 (價:{current_price} | {status})")
                
        except Exception as e:
            print(f"❌ {sid} 發生錯誤: {e}")
            still_watching.add(sid)
        
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
