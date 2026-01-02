import yfinance as yf
import requests
import os
import pandas as pd

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    # Discord
    requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    # LINE
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    requests.post(url, headers=headers, json=payload)

def check_breakthrough():
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    if not targets: return
    still_watching = set()
    
    for sid in targets:
        try:
            df = yf.download(f"{sid}.TW", period="10d", progress=False, auto_adjust=False)
            if df.empty: df = yf.download(f"{sid}.TWO", period="10d", progress=False, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            support_price = None
            for i in range(1, 4): 
                if df['Volume'].iloc[-i] >= (df['Volume'].iloc[-i-1] * 1.5):
                    support_price = df['Low'].iloc[-i]
                    break
            
            current_price = df['Close'].iloc[-1]
            if support_price and current_price < support_price:
                send_alert(f"🚨 跌破警報：{sid}\n現價 {current_price} 破支撐 {support_price:.1f}！")
            else:
                still_watching.add(sid)
        except: still_watching.add(sid)
        
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()

if __name__ == "__main__":
    check_breakthrough()
