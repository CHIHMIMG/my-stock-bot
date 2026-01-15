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
    print(f"🚀 啟動【全市場長上引線】最高成功率模式: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        dl = DataLoader()
        stock_info = dl.taiwan_stock_info()
        # 僅保留 4 位數代碼且排除金融股
        df_valid = stock_info[(stock_info['stock_id'].str.len() == 4) & 
                              (~stock_info['industry_category'].str.contains('金融'))].copy()
        name_dict = dict(zip(df_valid['stock_id'], df_valid['stock_name']))
        ids = df_valid['stock_id'].tolist()
        total_count = len(ids)
        print(f"📋 預計掃描總數: {total_count} 檔標的")
    except Exception as e:
        print(f"❌ 無法取得名單: {e}")
        return

    sent_list = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            sent_list = set(line.strip() for line in f.readlines())

    hits = []
    
    # 💡 終極優化：極小批次(5檔)，徹底降低被擋機率
    batch_size = 5
    for i in range(0, total_count, batch_size):
        batch = ids[i:i+batch_size]
        progress = round((i / total_count) * 100, 1)
        print(f"⏳ 進度: {progress}% | 正在掃描: {batch}")
        
        tickers = [f"{sid}.TW" for sid in batch] + [f"{sid}.TWO" for sid in batch]
        
        try:
            # 隨機長休息 3~6 秒，模擬真人行為
            time.sleep(random.uniform(3.0, 6.0))
            
            # 使用單線程模式 (threads=False) 以提高穩定性
            data = yf.download(tickers, period="3d", interval="1d", group_by='ticker', progress=False, threads=False)
            
            for sid in batch:
                if sid in sent_list: continue
                
                ticker = f"{sid}.TW"
                if ticker not in data.columns.levels[0] or data[ticker].dropna(subset=['Close']).empty:
                    ticker = f"{sid}.TWO"
                
                if ticker not in data.columns.levels[0]: continue
                
                df = data[ticker].dropna(subset=['Volume', 'High', 'Close'])
                if len(df) < 2: continue
                
                # 取得數值並確保格式
                try:
                    t_vol = float(df['Volume'].iloc[-1])
                    y_vol = float(df['Volume'].iloc[-2])
                    t_high = float(df['High'].iloc[-1])
                    t_close = float(df['Close'].iloc[-1])
                    
                    vol_ratio = t_vol / y_vol if y_vol > 0 else 0
                    drop_ratio = (t_high - t_close) / t_high if t_high > 0 else 0
                    t_vol_lots = int(t_vol / 1000)

                    # 篩選門檻：爆量1.5x / 回落4% / 量>5000張
                    if vol_ratio >= 1.5 and drop_ratio >= 0.04 and t_vol_lots >= 5000:
                        hits.append({
                            'id': sid, 'name': name_dict.get(sid, "未知"), 
                            'price': t_close, 'high': t_high, 
                            'vol': t_vol_lots, 'drop': round(drop_ratio * 100, 1),
                            'vol_x': round(vol_ratio, 1)
                        })
                        sent_list.add(sid)
                        print(f"🎯 命中標的: {sid} {name_dict.get(sid)}")
                except: continue
                    
        except Exception as e:
            print(f"⚠️ 遇到錯誤或限制，休息 15 秒: {e}")
            time.sleep(15)
            continue

    # 發送通知
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【全市場長上引線警報 - 高精準版】\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n   現價:{h['price']:.2f} (回落:{h['drop']}%)\n   總量:{h['vol']}張 | ⚡量增:{h['vol_x']}x\n"
        
        send_alert(msg)
        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(list(sent_list)))
    else:
        print("✅ 全市場掃描完成，未發現符合條件之爆量回落標的。")

if __name__ == "__main__":
    main()
