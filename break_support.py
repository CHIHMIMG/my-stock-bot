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
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    if not targets: return
        
    still_watching = set()
    print(f"⏰ 啟動【1分鐘級別】即時監控: {datetime.now().strftime('%H:%M:%S')}")

    for sid in targets:
        try:
            # 💡 關鍵修正：同時嘗試上市與上櫃，避免找不到資料
            df_now = yf.download(f"{sid}.TW", period="1d", interval="1m", progress=False)
            market = "TWSE"
            if df_now.empty:
                df_now = yf.download(f"{sid}.TWO", period="1d", interval="1m", progress=False)
                market = "OTC"
            
            if df_now.empty:
                still_watching.add(sid)
                continue

            # 抓取日線找支撐
            df_day = yf.download(f"{sid}.{'TW' if market=='TWSE' else 'TWO'}", period="10d", interval="1d", progress=False)
            
            # 💡 修正 Future Warning：改用 iloc[0] 讀取單一數值
            current_price = float(df_now['Close'].iloc[-1].iloc[0]) if isinstance(df_now['Close'].iloc[-1], pd.Series) else float(df_now['Close'].iloc[-1])
            
            # 判斷爆量支撐 (過去3天內 1.5倍爆量低點)
            support = None
            found_date = ""
            for i in range(2, 5):
                if df_day['Volume'].iloc[-i] >= (df_day['Volume'].iloc[-i-1] * 1.5):
                    support = float(df_day['Low'].iloc[-i])
                    found_date = df_day.index[-i].strftime('%m/%d')
                    break
            
            if support and current_price < support:
                msg = (f"🚨 【極速警報】跌破支撐：{sid}\n"
                       f"💰 即時價 {current_price:.2f} < {found_date} 支撐 {support:.2f}")
                send_alert(msg)
                print(f"🚨 {sid} 觸發通知")
            else:
                still_watching.add(sid)
                print(f"✅ {sid} 監控中 (價:{current_price})")
        except: still_watching.add(sid)
        
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
