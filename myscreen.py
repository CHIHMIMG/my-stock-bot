import yfinance as yf
import requests
import os
import pandas as pd
from datetime import datetime
from FinMind.data import DataLoader
import time

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
    except: pass
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def main():
    print(f"🚀 啟動【全市場】掃描 (排除金融股): {datetime.now().strftime('%Y-%m-%d')}")
    dl = DataLoader()
    
    # 1. 取得全台灣所有股票清單及其產業類別
    try:
        stock_info = dl.taiwan_stock_info()
        # 核心過濾：代號長度為4，且產業類別「不含」金融
        filtered_info = stock_info[
            (stock_info['stock_id'].str.len() == 4) & 
            (~stock_info['industry_category'].str.contains('金融'))
        ]
        all_ids = filtered_info['stock_id'].tolist()
        print(f"📊 排除金融股後，剩餘 {len(all_ids)} 檔標的進行掃描...")
    except Exception as e:
        print(f"⚠️ 無法取得清單: {e}")
        return

    final_selection = []
    
    # 2. 開始大規模掃描
    for i, sid in enumerate(all_ids):
        if i % 100 == 0: print(f"進度: {i}/{len(all_ids)}")
        
        try:
            ticker_sid = f"{sid}.TW"
            df = yf.download(ticker_sid, period="5d", progress=False, show_errors=False)
            
            if df.empty or len(df) < 2:
                ticker_sid = f"{sid}.TWO"
                df = yf.download(ticker_sid, period="5d", progress=False, show_errors=False)
            
            if df.empty or len(df) < 2: continue
            
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            price = float(today['Close'])
            vol_today = float(today['Volume']) / 1000 
            vol_yesterday = float(yesterday['Volume']) / 1000
            
            # --- 篩選條件：10<股價<100, 今日量>6000, 今日量>昨日量1.5倍 ---
            if 10 < price < 100 and vol_today >= 6000 and vol_today >= (vol_yesterday * 1.5):
                change = ((price - float(yesterday['Close'])) / float(yesterday['Close'])) * 100
                final_selection.append({
                    'id': sid,
                    'price': round(price, 2),
                    'vol': int(vol_today),
                    'diff': round(change, 2)
                })
                print(f"🎯 命中標的: {sid} (量增 {round(vol_today/vol_yesterday, 2)}倍)")
        except:
            continue

    # 3. 排序與發送
    if final_selection:
        final_selection = sorted(final_selection, key=lambda x: x['vol'], reverse=True)
        target_ids = [s['id'] for s in final_selection]
        with open('targets.txt', 'w') as f:
            f.write('\n'.join(target_ids))
        
        msg = f"📊 {datetime.now().strftime('%m/%d')} 全市場爆量精選(已過濾金融股)\n"
        msg += "------------------\n"
        for s in final_selection:
            msg += f"🔹 {s['id']}\n"
            msg += f"   收盤價: {s['price']}\n"
            msg += f"   漲跌幅: {s['diff']}%\n"
            msg += f"   成交量: {s['vol']}張\n"
        
        send_alert(msg)
        print(f"✅ 掃描完成，發現 {len(final_selection)} 檔。")
    else:
        print("今日無符合條件標的。")

if __name__ == "__main__":
    main()
