import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime

# --- 設定連線 ---
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

def get_valid_data(sid):
    """嘗試下載資料，自動判定上市櫃"""
    for suffix in ['.TW', '.TWO']:
        try:
            # 下載 1 分鐘 K 線 (即時價)
            df_now = yf.download(f"{sid}{suffix}", period="1d", interval="1m", progress=False)
            if df_now.empty: continue
            
            # 下載日線 (找支撐)
            df_day = yf.download(f"{sid}{suffix}", period="10d", interval="1d", progress=False)
            if df_day.empty: continue
            
            return df_now, df_day, suffix
        except: continue
    return None, None, None

def main():
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    still_watching = []
    print(f"🚀 [全新設計] 啟動監控: {datetime.now().strftime('%H:%M:%S')}")

    for sid in targets:
        try:
            df_now, df_day, suffix = get_valid_data(sid)
            if df_now is None:
                print(f"❌ {sid} 無法獲取數據，保留在清單")
                still_watching.append(sid)
                continue

            # 💡 核心改進：強制取最後一筆 Close 並轉換為純數字，防止 Series 歧義報錯
            raw_price = df_now['Close'].iloc[-1]
            current_price = float(raw_price.iloc[0] if hasattr(raw_price, '__len__') else raw_price)
            
            # 尋找最近 5 天內爆量 (1.5倍) 的 Low 作為支撐
            support = None
            found_date = ""
            for i in range(2, 6):
                v_today = float(df_day['Volume'].iloc[-i])
                v_prev = float(df_day['Volume'].iloc[-i-1])
                if v_today >= (v_prev * 1.5):
                    support = float(df_day['Low'].iloc[-i])
                    found_date = df_day.index[-i].strftime('%m/%d')
                    break
            
            if support and current_price < support:
                msg = f"🚨 【跌破警報】{sid}\n💰 現價 {current_price:.2f} < {found_date} 支撐 {support:.2f}"
                send_alert(msg)
                print(f"🚨 {sid} 觸發通知")
            else:
                still_watching.append(sid)
                print(f"✅ {sid} 監控中 ({current_price:.2f})")
        except Exception as e:
            print(f"⚠️ {sid} 掃描跳過: {e}")
            still_watching.append(sid)

    # 存回剩餘名單
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(still_watching))

if __name__ == "__main__":
    main()
