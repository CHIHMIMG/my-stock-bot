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

CACHE_FILE = 'sent_spikes.txt'

def send_alert(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
        payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def get_sent_list():
    if not os.path.exists(CACHE_FILE): return set()
    with open(CACHE_FILE, 'r') as f:
        return set(line.strip() for line in f.readlines())

def save_sent_list(sent_set):
    with open(CACHE_FILE, 'w') as f:
        f.write('\n'.join(list(sent_set)))

def main():
    print(f"🚀 啟動【全市場】爆量上引線掃描: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    mask = (stock_info['stock_id'].str.len() == 4) & (~stock_info['industry_category'].str.contains('金融'))
    valid_stocks = stock_info[mask].copy()
    name_dict = dict(zip(valid_stocks['stock_id'], valid_stocks['stock_name']))
    
    symbols = [f"{sid}.TW" for sid in valid_stocks['stock_id']] + [f"{sid}.TWO" for sid in valid_stocks['stock_id']]
    sent_list = get_sent_list()
    
    print(f"📥 下載數據中 (共 {len(valid_stocks)} 檔)...")
    data = yf.download(symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)

    hits = []
    print("🔎 正在分析符合條件的標的...")
    
    for sid in valid_stocks['stock_id']:
        if sid in sent_list: continue
        try:
            df = data[f"{sid}.TW"]
            if df.empty or df['Volume'].iloc[-1] == 0:
                df = data[f"{sid}.TWO"]
            
            if df.empty or len(df) < 2: continue
            
            yesterday_vol = df['Volume'].iloc[-2]
            today_vol = df['Volume'].iloc[-1]
            today_high = df['High'].iloc[-1]
            today_close = df['Close'].iloc[-1]
            
            if yesterday_vol == 0: continue

            vol_ratio = today_vol / yesterday_vol
            drop_ratio = (today_high - today_close) / today_high if today_high > 0 else 0

            # 💡 判斷門檻：量增 1.5 倍 且 高點回落 4%
            if vol_ratio >= 1.5 and drop_ratio >= 0.04:
                hits.append({
                    'id': sid,
                    'name': name_dict.get(sid, "未知"),
                    'price': today_close,
                    'high': today_high,
                    'drop': round(drop_ratio * 100, 1),
                    'vol_x': round(vol_ratio, 1)
                })
                sent_list.add(sid)
        except: continue

    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【全市場爆量上引線警報】\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n條件: 量增 1.5x & 回落 4%\n"
        msg += "─" * 15 + "\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n"
            msg += f"   💰 現價:{h['price']:.2f} (高點:{h['high']:.2f})\n"
            msg += f"   📉 高點回落:{h['drop']}% | 🔥量增:{h['vol_x']}倍\n"
            msg += f"   🔗 https://tw.tradingview.com/chart/?symbol=TWSE:{h['id']}\n"
            msg += "─" * 10 + "\n"
        
        send_alert(msg)
        save_sent_list(sent_list)
        print(f"✅ 成功命中 {len(hits)} 檔並發送警報。")
    else:
        print("ℹ️ 目前市場上無符合標的 (量增 < 1.5x 或 回落 < 4%)。")

if __name__ == "__main__":
    main()
