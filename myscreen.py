import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    """發送警報至 Discord 與 LINE"""
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
    except:
        pass
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except:
        pass

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
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"⏰ 執行監控 (排除今日爆量): {report_time}")

    for sid in targets:
        try:
            clean_sid = sid.strip()
            # 下載數據
            df = yf.download(f"{clean_sid}.TW", period="15d", progress=False, auto_adjust=False, multi_level_index=False)
            market_type = "TWSE"
            if df.empty or len(df) < 10:
                df = yf.download(f"{clean_sid}.TWO", period="15d", progress=False, auto_adjust=False, multi_level_index=False)
                market_type = "OTC"
            
            if df.empty:
                still_watching.add(clean_sid)
                continue

            current_price = float(df['Close'].iloc[-1])
            today_vol = int(df['Volume'].iloc[-1] / 1000)

            # --- 核心邏輯：從昨日往回找 3 天 (排除今日索引 -1) ---
            support_price = None
            found_date = ""

            # i=2(昨), 3(前), 4(大前)
            for i in range(2, 5): 
                vol_target = df['Volume'].iloc[-i]
                vol_prev = df['Volume'].iloc[-i-1]
                
                if vol_target >= (vol_prev * 1.5):
                    support_price = float(df['Low'].iloc[-i])
                    found_date = df.index[-i].strftime('%m/%d')
                    break 
            
            if support_price and current_price < support_price:
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market_type}:{clean_sid}"
                msg = (f"🚨 跌破爆量支撐：{clean_sid}\n"
                       f"💰 現價 {current_price:.2f} < {found_date} 低點 {support_price:.2f}\n"
                       f"📊 今日量：{today_vol}張\n"
                       f"🔗 線圖：{tv_url}")
                send_alert(msg)
                print(f"🚨 {clean_sid} 觸發！跌破 {found_date} 支撐")
            else:
                still_watching.add(clean_sid)
                status = f"支撐({found_date}):{support_price}" if support_price else "無爆量支撐"
                print(f"✅ {clean_sid} 正常 (現價:{current_price} | {status})")
                
        except Exception as e:
            still_watching.add(sid)
        
    # 修正最後一行的寫入邏輯
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
