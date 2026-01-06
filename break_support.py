import yfinance as yf
import requests
import os
import pandas as pd
import time
from datetime import datetime

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    """發送警報至 Discord 與 LINE"""
    # Discord 發送
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=10)
    except:
        pass
    
    # LINE 發送
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass

def check_breakthrough():
    """檢查庫存是否跌破支撐"""
    # 檢查監控清單是否存在
    if not os.path.exists('targets.txt'):
        print("⚠️ 找不到 targets.txt，請先放入股票代碼。")
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]
    
    if not targets:
        print("ℹ️ targets.txt 為空，目前無監控對象。")
        return
        
    still_watching = set()
    
    for sid in targets:
        try:
            # 使用 yfinance 抓取數據 (不使用還原股價以確保價格準確)
            df = yf.download(f"{sid}.TW", period="10d", progress=False, auto_adjust=False)
            if df.empty: 
                df = yf.download(f"{sid}.TWO", period="10d", progress=False, auto_adjust=False)
            
            # 處理 yfinance 可能產生的多層索引
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 尋找過去 3 天內的量增支撐位
            support_price = None
            for i in range(1, 4):
                if df['Volume'].iloc[-i] >= (df['Volume'].iloc[-i-1] * 1.5):
                    support_price = df['Low'].iloc[-i]
                    break
            
            current_price = df['Close'].iloc[-1]
            
            # 輸出目前檢查狀態到螢幕
            print(f"🔍 檢查中: {sid} | 現價: {current_price:.2f} | 支撐: {support_price:.1f if support_price else '無'}")

            # 判斷是否跌破支撐
            if support_price and current_price < support_price:
                msg = f"🚨 跌破警報：{sid}\n現價 {current_price:.2f} 跌破支撐 {support_price:.1f}！"
                send_alert(msg)
                print(f"🚩 {sid} 觸發警報，已移出清單。")
            else:
                still_watching.add(sid)
                
        except Exception as e:
            print(f"❌ 處理 {sid} 時出錯: {e}")
            still_watching.add(sid)
        
    # 更新 targets.txt (只保留尚未跌破的股票)
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

# --- 主程式：盤中每 5 分鐘循環 ---
if __name__ == "__main__":
    print("🚀 盤中監控系統啟動...")
    print("💡 監控時段：週一至週五 09:00 - 13:35")
    
    while True:
        now = datetime.now()
        
        # 1. 判斷是否在交易時間 (09:00 - 13:35)
        if now.weekday() < 5 and (9 * 60) <= (now.hour * 60 + now.minute) <= (13 * 60 + 35):
            print(f"\n⏰ --- 執行掃描: {now.strftime('%H:%M:%S')} ---")
            check_breakthrough()
            
            print(f"😴 掃描完畢，休眠 5 分鐘後再次執行...")
            time.sleep(300)  # 暫停 300 秒 (5 分鐘)
            
        # 2. 尚未開盤的等待邏輯
        elif now.weekday() < 5 and (now.hour * 60 + now.minute) < (9 * 60):
            print(f"💤 目前時間 {now.strftime('%H:%M:%S')}，尚未開盤，等待中...", end='\r')
            time.sleep(60)
            
        # 3. 超過收盤時間或週末，關閉程式
        else:
            print(f"\n🏁 當前時間 {now.strftime('%H:%M:%S')}，已過交易時段。")
            print("👋 程式自動關閉。")
            break
