import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime

# --- 您的設定 ---
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

def get_realtime_data(sid):
    # 自動判定上市(.TW)或上櫃(.TWO)
    for sfx in ['.TW', '.TWO']:
        try:
            df = yf.download(f"{sid}{sfx}", period="10d", interval="1d", progress=False)
            if df.empty: continue
            
            # 強制取值，解決截圖中的 Ambiguous 錯誤
            # 只取最後一天的 Close, Volume, Low
            last_idx = -1
            c = float(df['Close'].iloc[last_idx])
            v = float(df['Volume'].iloc[last_idx])
            l = float(df['Low'].iloc[last_idx])
            
            # 取得過去 5 天的支撐位 (爆量 1.5 倍)
            support = None
            for i in range(2, 6):
                vol_t = float(df['Volume'].iloc[-i])
                vol_y = float(df['Volume'].iloc[-i-1])
                if vol_t >= (vol_y * 1.5):
                    support = float(df['Low'].iloc[-i])
                    break
            
            return c, support, sfx
        except: continue
    return None, None, None

def main():
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    still_watching = []
    print(f"🚀 [斷根修復版] 啟動監控: {datetime.now().strftime('%H:%M:%S')}")

    for sid in targets:
        try:
            curr_price, support, sfx = get_realtime_data(sid)
            
            if curr_price and support and curr_price < support:
                msg = f"🚨 【警報】{sid} 跌破支撐\n💰 現價 {curr_price:.2f} < 爆量支撐 {support:.2f}"
                send_alert(msg)
                print(f"🚨 {sid} 觸發通知")
            else:
                still_watching.append(sid)
                print(f"✅ {sid} 監控中")
        except:
            still_watching.append(sid)

    with open('targets.txt', 'w') as f:
        f.write('\n'.join(still_watching))

if __name__ == "__main__":
    main()
