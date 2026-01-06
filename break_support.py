import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime

# --- 設定區 ---
# 提醒：請確認這些 Token 在 GitHub Secrets 或直接在此處填寫正確
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    """發送警報至 Discord 與 LINE"""
    # Discord
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=10)
    except:
        pass
    # LINE
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass

def check_breakthrough():
    if not os.path.exists('targets.txt'):
        print("找不到 targets.txt")
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    if not targets:
        print("監控清單為空")
        return
        
    still_watching = set()
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"⏰ 執行時間: {report_time}")

    for sid in targets:
        try:
            # 1. 嘗試下載上市 (.TW)，關閉自動調整，強制單層索引
            df = yf.download(f"{sid}.TW", period="15d", progress=False, auto_adjust=False, multi_level_index=False)
            
            # 2. 如果沒資料，嘗試下載上櫃 (.TWO)
            if df.empty:
                df = yf.download(f"{sid}.TWO", period="15d", progress=False, auto_adjust=False, multi_level_index=False)
            
            if df.empty:
                print(f"⚠️ 無法取得 {sid} 資料，略過")
                still_watching.add(sid)
                continue

            # 3. 數據核對與驗證 (針對抽查股票)
            current_price = float(df['Close'].iloc[-1])
            last_vol = int(df['Volume'].iloc[-1] / 1000)
            print(f"🔍 [驗證] {sid}: 股價 {current_price:.2f} | 量 {last_vol}張")

            # 4. 尋找過去 3 天內的爆量支撐位
            support_price = None
            for i in range(1, 4):
                vol_today = df['Volume'].iloc[-i]
                vol_prev = df['Volume'].iloc[-i-1]
                # 判斷量增 1.5 倍
                if vol_today >= (vol_prev * 1.5):
                    support_price = float(df['Low'].iloc[-i])
                    break
            
            # 5. 判斷是否跌破支撐
            if support_price and current_price < support_price:
                # 決定市場分類以提供正確線圖連結
                market = "TWSE" if f"{sid}.TW" in df.index else "OTC"
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market}:{sid}"
                
                msg = (f"🚨 跌破警報：{sid}\n"
                       f"💰 現價 {current_price:.2f} 跌破支撐 {support_price:.1f}\n"
                       f"📊 數據日期：{df.index[-1].strftime('%m/%d')}\n"
                       f"🔗 線圖：{tv_url}")
                
                send_alert(msg)
                print(f"🚨 {sid} 已發送警報並移除")
            else:
                still_watching.add(sid)
                
        except Exception as e:
            print(f"❌ 處理 {sid} 時發生錯誤: {e}")
            still_watching.add(sid)
        
    # 寫回未觸發的股票，避免重複發報
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
