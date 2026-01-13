import yfinance as yf
import requests
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
        url = 'https://api.line.me/v2/bot/message/push'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
        payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def main():
    print(f"🚀 啟動【全市場】爆量上引線掃描: {datetime.now().strftime('%H:%M')}")
    
    # 1. 取得全台股精準清單 (含名稱對照)
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    # 過濾：代號 4 碼、排除金融、排除 ETF
    mask = (stock_info['stock_id'].str.len() == 4) & (~stock_info['industry_category'].str.contains('金融'))
    valid_stocks = stock_info[mask].copy()
    
    # 建立名稱字典，確保 ID 與 Name 絕對吻合
    name_dict = dict(zip(valid_stocks['stock_id'], valid_stocks['stock_name']))
    
    # 準備批次下載清單
    symbols = [f"{sid}.TW" for sid in valid_stocks['stock_id']] + [f"{sid}.TWO" for sid in valid_stocks['stock_id']]

    # 2. 批次下載數據
    print(f"📥 正在同步下載 {len(valid_stocks)} 檔即時數據...")
    # 使用 group_by='ticker' 確保數據歸類正確
    data = yf.download(symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)

    hits = []
    
    for sid in valid_stocks['stock_id']:
        try:
            # 判斷是在上市還是上櫃
            df = data[f"{sid}.TW"]
            if df.empty or df['Volume'].iloc[-1] == 0:
                df = data[f"{sid}.TWO"]
            
            if df.empty or len(df) < 2: continue
            
            # 數據取值 (iloc[-1] 為今日即時, iloc[-2] 為昨日)
            yesterday_vol = df['Volume'].iloc[-2]
            today_vol = df['Volume'].iloc[-1]
            today_high = df['High'].iloc[-1]
            today_close = df['Close'].iloc[-1]
            
            if yesterday_vol == 0: continue

            # --- 核心邏輯 ---
            vol_ratio = today_vol / yesterday_vol
            drop_ratio = (today_high - today_close) / today_high if today_high > 0 else 0

            # 條件：量增 2 倍以上 且 高點回落 5% 以上
            if vol_ratio >= 2.0 and drop_ratio >= 0.05:
                hits.append({
                    'id': sid,
                    'name': name_dict.get(sid, "未知"),
                    'price': today_close,
                    'high': today_high,
                    'drop': round(drop_ratio * 100, 1),
                    'vol_x': round(vol_ratio, 1)
                })
        except: continue

    # 3. 發送格式化警報
    if hits:
        # 按回落幅度排序，抓最嚴重的
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        
        msg = f"⚠️ 【全市場爆量上引線警報】\n(排除今日金融股)\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n"
        msg += "─" * 15 + "\n"
        for h in hits[:15]: # 最多顯示 15 檔
            msg += f"🔹 {h['id']} {h['name']}\n"
            msg += f"   💰 現價:{h['price']:.2f} (高點:{h['high']:.2f})\n"
            msg += f"   📉 高點回落:{h['drop']}% | 🔥量增:{h['vol_x']}倍\n"
            msg += f"   🔗 https://tw.tradingview.com/chart/?symbol=TWSE:{h['id']}\n"
            msg += "─" * 10 + "\n"
        
        send_alert(msg)
        print(f"✅ 命中 {len(hits)} 檔，警報已發送。")
    else:
        print("✅ 掃描完成，目前無標的符合爆量回落條件。")

if __name__ == "__main__":
    main()
