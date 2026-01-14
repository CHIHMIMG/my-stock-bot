import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime

# --- 您的連線設定 ---
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

def get_data(sid):
    # 💡 核心改進：自動嘗試上市(.TW)或上櫃(.TWO)後綴，解決截圖中的 404 錯誤
    for sfx in ['.TW', '.TWO']:
        try:
            df_now = yf.download(f"{sid}{sfx}", period="1d", interval="1m", progress=False)
            if df_now.empty: continue
            df_day = yf.download(f"{sid}{sfx}", period="10d", interval="1d", progress=False)
            if not df_day.empty: return df_now, df_day, sfx
        except: continue
    return None, None, None

def main():
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    watching = []
    print(f"⏰ [新設計] 啟動監控: {datetime.now().strftime('%H:%M:%S')}")

    for sid in targets:
        try:
            df_now, df_day, _ = get_data(sid)
            if df_now is None: 
                watching.append(sid)
                continue

            # 💡 核心改進：強制取值，徹底封殺截圖中的「Series is ambiguous」報錯
            close_val = df_now['Close'].iloc[-1]
            current_price = float(close_val.iloc[0]) if isinstance(close_val, pd.Series) else float(close_val)
            
            support = None
            f_date = ""
            for i in range(2, 6):
                vt = float(df_day['Volume'].iloc[-i])
                vp = float(df_day['Volume'].iloc[-i-1])
                if vt >= (vp * 1.5): # 爆量支撐條件
                    support = float(df_day['Low'].iloc[-i])
                    f_date = df_day.index[-i].strftime('%m/%d')
                    break
            
            if support and current_price < support:
                msg = f"🚨 【盤中警報】跌破支撐：{sid}\n💰 現價 {current_price:.2f} < {f_date} 支撐 {support:.2f}"
                send_alert(msg)
            else:
                watching.append(sid)
                print(f"✅ {sid} 正常 (價:{current_price:.2f})")
        except Exception as e:
            watching.append(sid)
            print(f"⚠️ {sid} 掃描異常，略過。")

    with open('targets.txt', 'w') as f:
        f.write('\n'.join(watching))

if __name__ == "__main__":
    main()
