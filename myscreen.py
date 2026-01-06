import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

VOL_THRESHOLD = 6000  # 成交量門檻：6000張
VOL_RATIO = 1.5       # 量增倍數：1.5倍
PRICE_LIMIT = 100     # 股價門檻：100元以下

def send_notifications(msg):
    """發送通知到 Discord 與 LINE"""
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=20)
    except:
        pass
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=20)
    except:
        pass

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動掃描系統 | 門檻: {PRICE_LIMIT}元以下 | {report_time}")
    
    # 獲取台股所有股票清單
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    unique_list = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].drop_duplicates().values.tolist()
    
    hits_msgs = []
    hits_sids = set()
    
    for sid, name in unique_list:
        try:
            # 修正 1: multi_level_index=False 確保欄位是單層，不會抓錯 Close
            # 修正 2: auto_adjust=False 抓取真實股價，不使用還原股價
            df = yf.download(f"{sid}.TW", period="65d", progress=False, auto_adjust=False, multi_level_index=False)
            if df.empty or len(df) < 20:
                df = yf.download(f"{sid}.TWO", period="65d", progress=False, auto_adjust=False, multi_level_index=False)
            
            if df.empty: continue

            # 抓取最新與前一天的資料
            today_data = df.iloc[-1]
            yesterday_data = df.iloc[-2]
            
            # --- 抽查驗證功能 ---
            # 當遇到華邦電(2344)或零壹(3029)時，強制在終端機輸出數據供核對
            if sid in ['2344', '3029']:
                print(f"🔍 [數據核對] {sid} {name}: 日期={df.index[-1].date()}, 收盤={today_data['Close']:.2f}, 量={int(today_data['Volume']/1000)}張")

            close_price = float(today_data['Close'])
            yesterday_close = float(yesterday_data['Close'])
            today_vol = float(today_data['Volume']) / 1000 
            yesterday_vol = float(yesterday_data['Volume']) / 1000
            
            # 技術指標：計算 5, 20, 60 日均線
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # 篩選邏輯：
            # 1. 股價在限制內 
            # 2. 今天爆量 (大於門檻且大於昨天的 1.5 倍)
            # 3. 股價站穩在所有均線之上 (轉強訊號)
            if (close_price <= PRICE_LIMIT and
                today_vol >= VOL_THRESHOLD and 
                today_vol >= (yesterday_vol * VOL_RATIO) and 
                close_price >= max(ma5, ma20, ma60)):
                
                p_percent = ((close_price - yesterday_close) / yesterday_close) * 100
                icon = "🔴" if p_percent > 0 else "🟢"
                growth = round(today_vol / yesterday_vol, 1)
                
                # TradingView 連結設定
                tv_market = "TWSE" if f"{sid}.TW" in df.index else "OTC"
                tv_url = f"https://tw.tradingview.com/chart/?symbol={tv_market}:{sid}"
                
                res = f"{icon} {sid} {name}\n💰 股價: {close_price:.2f} ({p_percent:+.2f}%)\n📊 成交: {int(today_vol)}張 ({growth}x)\n🔗 線圖: {tv_url}\n"
                hits_msgs.append(res)
                hits_sids.add(sid)
                print(f"✨ 符合條件: {sid} {name} | 價格: {close_price:.2f}")

        except Exception as e:
            # 遇到錯誤跳過
            continue
            
    # 將符合標的寫入 targets.txt，供另一個監控腳本使用
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(hits_sids))))
    
    # 彙整發送通知
    if hits_msgs:
        header = f"🔥 【台股爆量轉強名單】\n⏰ {report_time}\n篩選: {PRICE_LIMIT}元以下 + 多頭排列\n" + "─" * 15 + "\n"
        # 每 5 檔發一個訊息，避免訊息過長被系統截斷
        for i in range(0, len(hits_msgs), 5):
            chunk = "\n".join(hits_msgs[i:i + 5])
            send_notifications(header + chunk if i == 0 else chunk)
        print(f"✅ 掃描完成，共發現 {len(hits_msgs)} 檔標的。")
    else:
        print("掃描完成，今日無符合標的。")
        # send_notifications(f"📊 掃描完成 ({report_time})，今日無符合標的。")

if __name__ == "__main__":
    screen_stocks()
