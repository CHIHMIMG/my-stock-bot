import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from FinMind.data import DataLoader
import os
import time
import random

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
    print(f"🚀 啟動【精選強勢股】上引線掃描: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    dl = DataLoader()
    
    # 1. 取得基本名單並排除金融股
    stock_info = dl.taiwan_stock_info()
    df_info = stock_info[(stock_info['stock_id'].str.len() == 4) & 
                         (~stock_info['industry_category'].str.contains('金融'))].copy()
    
    # 2. 取得今日成交資訊進行初步過濾 (過濾 股價>20, 成交量>6000)
    # 注意：盤中時 FinMind 的成交量為即時參考
    try:
        # 抓取最近一個交易日的成交數據
        today_str = datetime.now().strftime('%Y-%m-%d')
        df_price = dl.taiwan_stock_daily_prev_views(date=today_str)
        
        # 合併篩選條件
        valid_ids = df_price[
            (df_price['close'] >= 20) & 
            (df_price['vol'] >= 6000) # FinMind 的 vol 通常是張數
        ]['stock_id'].tolist()
        
        # 最終監控名單 = 非金融股 且 符合量價條件
        final_list = [sid for sid in df_info['stock_id'].tolist() if sid in valid_ids]
        name_dict = dict(zip(df_info['stock_id'], df_info['stock_name']))
        
        print(f"✅ 過濾完成！監控標的已從 {len(stock_info)} 縮減至 {len(final_list)} 檔。")
    except Exception as e:
        print(f"⚠️ 預篩選失敗 (可能未開盤)，將執行全名單掃描。錯誤: {e}")
        final_list = df_info['stock_id'].tolist()
        name_dict = dict(zip(df_info['stock_id'], df_info['stock_name']))

    # 讀取快取
    sent_list = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            sent_list = set(line.strip() for line in f.readlines())

    hits = []
    
    # 3. 開始掃描
    batch_size = 15 # 因為總量變少，批次可以稍微調大一點
    for i in range(0, len(final_list), batch_size):
        batch = final_list[i:i+batch_size]
        tickers = [f"{sid}.TW" for sid in batch] + [f"{sid}.TWO" for sid in batch]
        
        try:
            time.sleep(random.uniform(1.5, 3.0)) # 保持適度禮貌
            data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False)
            
            for sid in batch:
                if sid in sent_list: continue
                ticker = f"{sid}.TW"
                if ticker not in data.columns.levels[0] or data[ticker].dropna().empty:
                    ticker = f"{sid}.TWO"
                
                if ticker not in data.columns.levels[0]: continue
                
                df = data[ticker].dropna()
                if len(df) < 2: continue
                
                t_vol = float(df['Volume'].iloc[-1])
                y_vol = float(df['Volume'].iloc[-2])
                t_high = float(df['High'].iloc[-1])
                t_close = float(df['Close'].iloc[-1])
                
                vol_ratio = t_vol / y_vol if y_vol > 0 else 0
                drop_ratio = (t_high - t_close) / t_high if t_high > 0 else 0
                t_vol_lots = int(t_vol / 1000)

                # 警報門檻 (可根據需求微調)
                if vol_ratio >= 1.5 and drop_ratio >= 0.04:
                    hits.append({
                        'id': sid, 'name': name_dict.get(sid, "未知"), 
                        'price': t_close, 'high': t_high, 
                        'vol': t_vol_lots, 'drop': round(drop_ratio * 100, 1), 'vol_x': round(vol_ratio, 1)
                    })
                    sent_list.add(sid)
        except: continue

    # 4. 發送警報
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【精選爆量回落通知】\n篩選: 股價>20 / 量>6000 / 非金融\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n   價:{h['price']:.2f} (回:{h['drop']}%)\n   量:{h['vol']}張 | ⚡增:{h['vol_x']}x\n"
        send_alert(msg)
        with open(CACHE_FILE, 'w') as f: f.write('\n'.join(list(sent_list)))
    else:
        print("✅ 掃描完畢，目前無符合條件標的。")

if __name__ == "__main__":
    main()
