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
    print(f"🚀 啟動【全市場】精準掃描: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. 取得全台股資訊
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    df_valid = stock_info[(stock_info['stock_id'].str.len() == 4) & 
                          (~stock_info['industry_category'].str.contains('金融'))].copy()
    
    name_dict = dict(zip(df_valid['stock_id'], df_valid['stock_name']))
    sent_list = get_sent_list()
    
    # 2. 下載即時數據
    tw_symbols = [f"{sid}.TW" for sid in df_valid['stock_id']]
    two_symbols = [f"{sid}.TWO" for sid in df_valid['stock_id']]

    print(f"📥 正在下載上市/上櫃數據 (含 5000 張門檻過濾)...")
    data_tw = yf.download(tw_symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)
    data_two = yf.download(two_symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)

    hits = []
    
    for sid in df_valid['stock_id']:
        if sid in sent_list: continue
        
        ticker_tw = f"{sid}.TW"
        ticker_two = f"{sid}.TWO"
        
        df = pd.DataFrame()
        if ticker_tw in data_tw.columns.levels[0]:
            df = data_tw[ticker_tw]
        if (df.empty or df['Volume'].isnull().all()) and ticker_two in data_two.columns.levels[0]:
            df = data_two[ticker_two]
            
        if df.empty or len(df) < 2: continue
        
        try:
            y_vol = df['Volume'].iloc[-2]
            t_vol = df['Volume'].iloc[-1]
            t_high = df['High'].iloc[-1]
            t_close = df['Close'].iloc[-1]
            
            if pd.isna(y_vol) or y_vol == 0: continue

            # --- 綜合判斷邏輯 ---
            # 1. 爆量倍數 (1.5倍)
            vol_ratio = t_vol / y_vol
            # 2. 高點回落幅度 (4%)
            drop_ratio = (t_high - t_close) / t_high if t_high > 0 else 0
            # 3. 今日成交量門檻 (至少 5000 張)
            # yfinance 的 Volume 單位是「股」，所以 5000 張 = 5,000,000 股
            today_volume_shares = t_vol
            
            if vol_ratio >= 1.5 and drop_ratio >= 0.04 and today_volume_shares >= 5000000:
                hits.append({
                    'id': sid, 
                    'name': name_dict.get(sid, "未知"), 
                    'price': t_close, 
                    'high': t_high, 
                    'vol': int(today_volume_shares / 1000), # 轉為張數顯示
                    'drop': round(drop_ratio * 100, 1), 
                    'vol_x': round(vol_ratio, 1)
                })
                sent_list.add(sid)
        except: continue

    # 3. 發送報告
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【全市場爆量上引線警報】\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n門檻: 爆量1.5x / 回落4% / 量>5000張\n"
        msg += "─" * 15 + "\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n"
            msg += f"   💰 現價:{h['price']:.2f} (高點:{h['high']:.2f})\n"
            msg += f"   📊 今日總量: {h['vol']} 張\n"
            msg += f"   📉 高點回落:{h['drop']}% | 🔥量增:{h['vol_x']}倍\n"
            msg += f"   🔗 https://tw.tradingview.com/chart/?symbol=TWSE:{h['id']}\n"
            msg += "─" * 10 + "\n"
        
        send_alert(msg)
        save_sent_list(sent_list)
        print(f"✅ 命中 {len(hits)} 檔符合大成交量條件標的")
    else:
        print("ℹ️ 掃描完畢，目前無符合 5000 張且回落之標的。")

if __name__ == "__main__":
    main()
