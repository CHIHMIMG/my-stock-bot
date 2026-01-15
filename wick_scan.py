import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
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
    print(f"🚀 啟動【全市場長上引線】穩定掃描: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 取得全市場名單
    try:
        dl = DataLoader()
        stock_info = dl.taiwan_stock_info()
        # 僅保留 4 位數代碼且排除金融股
        df_valid = stock_info[(stock_info['stock_id'].str.len() == 4) & 
                              (~stock_info['industry_category'].str.contains('金融'))].copy()
        name_dict = dict(zip(df_valid['stock_id'], df_valid['stock_name']))
        ids = df_valid['stock_id'].tolist()
    except Exception as e:
        print(f"❌ 無法取得名單: {e}")
        return

    # 讀取今日已通知名單
    sent_list = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            sent_list = set(line.strip() for line in f.readlines())

    hits = []
    
    # 💡 核心改進：小批次 (15檔) 配合隨機延遲，防止被 Yahoo 封鎖
    batch_size = 15
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        print(f"📦 正在掃描 ({i}/{len(ids)}) ...")
        
        # 準備上市與上櫃兩種可能
        tickers = [f"{sid}.TW" for sid in batch] + [f"{sid}.TWO" for sid in batch]
        
        try:
            # 隨機休息 1~2 秒，模擬真人行為
            time.sleep(random.uniform(1.0, 2.5))
            
            data = yf.download(tickers, period="3d", interval="1d", group_by='ticker', progress=False)
            
            for sid in batch:
                if sid in sent_list: continue
                
                # 自動判定哪個後綴有數據
                ticker = f"{sid}.TW"
                if ticker not in data.columns.levels[0] or data[ticker].dropna().empty:
                    ticker = f"{sid}.TWO"
                
                if ticker not in data.columns.levels[0]: continue
                
                df = data[ticker].dropna()
                if len(df) < 2: continue
                
                # 取得今日與昨日數據 (強制轉為 float)
                t_vol = float(df['Volume'].iloc[-1])
                y_vol = float(df['Volume'].iloc[-2])
                t_high = float(df['High'].iloc[-1])
                t_close = float(df['Close'].iloc[-1])
                
                # 門檻計算
                vol_ratio = t_vol / y_vol if y_vol > 0 else 0
                drop_ratio = (t_high - t_close) / t_high if t_high > 0 else 0
                t_vol_lots = int(t_vol / 1000)

                # 🚀 篩選門檻：量增1.5倍 & 回落>4% & 總張數>5000張
                if vol_ratio >= 1.5 and drop_ratio >= 0.04 and t_vol_lots >= 5000:
                    hits.append({
                        'id': sid, 'name': name_dict.get(sid, "未知"), 
                        'price': t_close, 'high': t_high, 
                        'vol': t_vol_lots, 'drop': round(drop_ratio * 100, 1),
                        'vol_x': round(vol_ratio, 1)
                    })
                    sent_list.add(sid)
                    print(f"🎯 發現標的: {sid} {name_dict.get(sid)}")
                    
        except Exception as e:
            print(f"⚠️ 批次執行錯誤 (跳過本組): {e}")
            time.sleep(5) # 出錯時休息久一點
            continue

    # 發送通知
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【全市場長上引線警報】\n門檻: 爆量1.5x / 高點回落4% / 量>5000張\n"
        for h in hits[:15]: # 最多顯示 15 檔
            msg += f"🔹 {h['id']} {h['name']}\n   現價:{h['price']:.2f} (高:{h['high']:.2f})\n   總量:{h['vol']}張 | ⚡量增:{h['vol_x']}x | 📉回落:{h['drop']}%\n"
        
        send_alert(msg)
        
        # 更新快取
        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(list(sent_list)))
    else:
        print("✅ 掃描完成，今日無符合條件標的。")

if __name__ == "__main__":
    main()
