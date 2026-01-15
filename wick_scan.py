import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
from FinMind.data import DataLoader
import os

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

CACHE_FILE = 'sent_wick_spikes.txt'

def send_alert(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
        payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def main():
    print(f"🚀 啟動【全市場上引線】掃描: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    df_valid = stock_info[(stock_info['stock_id'].str.len() == 4) & (~stock_info['industry_category'].str.contains('金融'))].copy()
    name_dict = dict(zip(df_valid['stock_id'], df_valid['stock_name']))
    
    sent_list = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            sent_list = set(line.strip() for line in f.readlines())

    hits = []
    ids = df_valid['stock_id'].tolist()
    
    # 分批抓取 (每批 50 檔) 避免 404 報錯
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        tickers = [f"{sid}.TW" for sid in batch] + [f"{sid}.TWO" for sid in batch]
        data = yf.download(tickers, period="3d", interval="1d", group_by='ticker', progress=False, threads=True)
        
        for sid in batch:
            if sid in sent_list: continue
            ticker = f"{sid}.TW"
            if ticker not in data.columns.levels[0] or data[ticker].dropna().empty:
                ticker = f"{sid}.TWO"
            
            try:
                df = data[ticker].dropna()
                if len(df) < 2: continue
                
                vol_ratio = float(df['Volume'].iloc[-1]) / float(df['Volume'].iloc[-2])
                drop = (float(df['High'].iloc[-1]) - float(df['Close'].iloc[-1])) / float(df['High'].iloc[-1])
                
                # 門檻：爆量1.5x / 高點回落4% / 量>5000張
                if vol_ratio >= 1.5 and drop >= 0.04 and (float(df['Volume'].iloc[-1])/1000) >= 5000:
                    hits.append({'id': sid, 'name': name_dict.get(sid, ""), 'price': float(df['Close'].iloc[-1]), 'drop': round(drop*100, 1), 'vol_x': round(vol_ratio, 1)})
                    sent_list.add(sid)
            except: continue

    if hits:
        msg = f"⚠️ 【全市場長上引線警報】\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n   現價:{h['price']:.2f} (回落:{h['drop']}% | 量增:{h['vol_x']}x)\n"
        send_alert(msg)
        with open(CACHE_FILE, 'w') as f: f.write('\n'.join(list(sent_list)))

if __name__ == "__main__": main()
