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
    print(f"⏰ 執行盤中監控: {report_time}")

    for sid in targets:
        try:
            clean_sid = sid.strip()
            # 1. 優先嘗試下載上市 (.TW)
            market_type = "TWSE"
            df = yf.download(f"{clean_sid}.TW", period="15d", progress=False, auto_adjust=False, multi_level_index=False)
            
            # 2. 若無資料，嘗試下載上櫃 (.TWO)
            if df.empty or len(df) < 5:
                df = yf.download(f"{clean_sid}.TWO", period="15d", progress=False, auto_adjust=False, multi_level_index=False)
                market_type = "OTC"
            
            if df.empty:
                print(f"⚠️ 無法取得 {clean_sid} 資料")
                still_watching.add(clean_sid)
                continue

            # 3. 💡 新增：抓取股票名稱 (Ticker Info)
            ticker = yf.Ticker(f"{clean_sid}.TW" if market_type == "TWSE" else f"{clean_sid}.TWO")
            s_name = ticker.info.get('shortName', clean_sid)

            current_price = float(df['Close'].iloc[-1])
            last_vol = int(df['Volume'].iloc[-1] / 1000)

            # 4. 尋找過去 3 天內的爆量支撐位
            support_price = None
            for i in range(1, 4):
                vol_today = df['Volume'].iloc[-i]
                vol_prev = df['Volume'].iloc[-i-1]
                if vol_today >= (vol_prev * 1.5):
                    support_price = float(df['Low'].iloc[-i])
                    break
            
            # 5. 判斷是否跌破支撐
            if support_price and current_price < support_price:
                # 💡 修正：使用正確的市場分類，確保 TradingView 不會是一片空白
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market_type}:{clean_sid}"
                
                msg = (f"🚨 跌破警報：{clean_sid} {s_name}\n"
                       f"💰 現價 {current_price:.2f} 跌破支撐 {support_price:.1f}\n"
                       f"📊 數據日期：{df.index[-1].strftime('%m/%d')}\n"
                       f"🔗 線圖：{tv_url}")
                
                send_alert(msg)
                print(f"🚨 {clean_sid} {s_name} 已發送警報並移出清單")
            else:
                still_watching.add(clean_sid)
                print(f"✅ {clean_sid} {s_name} 守住支撐 ({current_price:.2f} > {support_price if support_price else 'N/A'})")
                
        except Exception as e:
            print(f"❌ 處理 {sid} 時發生錯誤: {e}")
            still_watching.add(sid)
        
    # 寫回未觸發的股票
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
