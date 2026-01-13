import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from FinMind.data import DataLoader
import os

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

# 緩存文件，紀錄已提醒過的標的
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
    """讀取今日已發送過的標的清單"""
    if not os.path.exists(CACHE_FILE): return set()
    with open(CACHE_FILE, 'r') as f:
        return set(line.strip() for line in f.readlines())

def save_sent_list(sent_set):
    """保存已發送標的"""
    with open(CACHE_FILE, 'w') as f:
        f.write('\n'.join(list(sent_set)))

def main():
    print(f"🚀 啟動【全市場】爆量上引線掃描: {datetime.now().strftime('%H:%M')}")
    
    # 1. 取得全台股精準名稱對照表
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    mask = (stock_info['stock_id'].str.len() == 4) & (~stock_info['industry_category'].str.contains('金融'))
    valid_stocks = stock_info[mask].copy()
    name_dict = dict(zip(valid_stocks['stock_id'], valid_stocks['stock_name']))
    
    # 2. 準備數據
    symbols = [f"{sid}.TW" for sid in valid_stocks['stock_id']] + [f"{sid}.TWO" for sid in valid_stocks['stock_id']]
    sent_list = get_sent_list()
    
    print(f"📥 正在下載全市場 {len(valid_stocks)} 檔即時數據...")
    data = yf.download(symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)

    hits = []
    current_time = datetime.now().strftime('%Y-%m-%d')

    for sid in valid_stocks['stock_id']:
        # 如果這檔股票今天已經發過警報，就跳過
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

            # --- 判斷邏輯 ---
            vol_ratio = today_vol / yesterday_vol
            drop_ratio = (today_high - today_close) / today_high if today_high > 0 else 0

            # 💡 修正：量增 1.5 倍 且 高點回落 5%
            if vol_ratio >= 1.5 and drop_ratio >= 0.05:
                hits.append({
                    'id': sid,
                    'name': name_dict.get(sid, "未知"),
                    'price': today_close,
                    'high': today_high,
                    'drop': round(drop_ratio * 100, 1),
                    'vol_x': round(vol_ratio, 1)
                })
                sent_list.add(sid) # 加入已發送清單
        except: continue

    # 3. 發送報告並保存清單
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【全市場爆量上引線警報】\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n條件: 量增 1.5x & 回落 5%\n"
        msg += "─" * 15 + "\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n"
            msg += f"   💰 現價:{h['price']:.2f} (高點:{h['high']:.2f})\n"
            msg += f"   📉 高點回落:{h['drop']}% | 🔥量增:{h['vol_x']}倍\n"
            msg += f"   🔗 https://tw.tradingview.com/chart/?symbol=TWSE:{h['id']}\n"
            msg += "─" * 10 + "\n"
        
        send_alert(msg)
        save_sent_list(sent_list) # 儲存已提醒標的，下次執行就不會重複
        print(f"✅ 成功命中 {len(hits)} 檔，已更新 sent_spikes.txt")
    else:
        print("今日無新符合標的")

if __name__ == "__main__":
    main()
