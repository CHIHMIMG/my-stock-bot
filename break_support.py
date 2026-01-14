import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
from FinMind.data import DataLoader
import os

# --- 您的連線設定 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

CACHE_FILE = 'sent_alerts.txt' # 避免同一天重複通知

def send_alert(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
        payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def main():
    print(f"🚀 開始全市場掃描: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. 自動取得全市場股票名單 (排除金融、權證)
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    df_valid = stock_info[(stock_info['stock_id'].str.len() == 4) & 
                          (~stock_info['industry_category'].str.contains('金融'))].copy()
    
    ids = df_valid['stock_id'].tolist()
    name_dict = dict(zip(df_valid['stock_id'], df_valid['stock_name']))

    # 讀取快取
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            sent_list = set(line.strip() for line in f.readlines())
    else:
        sent_list = set()

    found_hits = []

    # 2. 分批掃描 (全市場 1700 檔，每批 100 檔避免超時)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        # 同時下載上市與上櫃資料
        tickers = [f"{sid}.TW" for sid in batch] + [f"{sid}.TWO" for sid in batch]
        data = yf.download(tickers, period="6d", interval="1d", group_by='ticker', progress=False, threads=True)
        
        for sid in batch:
            if sid in sent_list: continue
            
            # 判斷市場後綴
            ticker = f"{sid}.TW"
            if ticker not in data.columns.levels[0] or data[ticker].dropna().empty:
                ticker = f"{sid}.TWO"
            
            try:
                df = data[ticker].dropna()
                if len(df) < 4: continue
                
                # --- 條件：尋找前 3 天是否有「爆量支撐」 ---
                support_price = None
                for d in range(1, 4): 
                    vol_today = df['Volume'].iloc[-d-1]
                    vol_yesterday = df['Volume'].iloc[-d-2]
                    # 爆量條件：當日量 > 昨日量 1.5 倍
                    if vol_today > vol_yesterday * 1.5:
                        support_price = float(df['Low'].iloc[-d-1])
                        break
                
                if support_price:
                    current_price = float(df['Close'].iloc[-1])
                    # 條件：現價跌破支撐
                    if current_price < support_price:
                        name = name_dict.get(sid, "")
                        found_hits.append(f"🔹 {sid} {name}\n   📉 現價 {current_price:.2f} < 爆量支撐 {support_price:.2f}")
                        sent_list.add(sid)
            except: continue

    # 3. 發送結果
    if found_hits:
        msg = f"⚠️ 【全市場盤中跌破通知】\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n"
        msg += "\n".join(found_hits[:15]) # 限制長度
        send_alert(msg)
        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(list(sent_list)))
        print(f"✅ 已發送 {len(found_hits)} 檔通知")
    else:
        print("ℹ️ 掃描結束，沒有新發現。")

if __name__ == "__main__":
    main()
