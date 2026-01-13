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
    
    # 過濾：只取 4 碼代號、排除金融股
    df_valid = stock_info[(stock_info['stock_id'].str.len() == 4) & 
                          (~stock_info['industry_category'].str.contains('金融'))].copy()
    
    name_dict = dict(zip(df_valid['stock_id'], df_valid['stock_name']))
    sent_list = get_sent_list()
    
    # 2. 分批建立下載清單 (為了避免 KeyError，我們嘗試對所有代號都下載上市與上櫃後再過濾)
    # 這裡採用更穩健的方法：將所有代號加入清單，並透過下載後的結果自動過濾
    tw_symbols = [f"{sid}.TW" for sid in df_valid['stock_id']]
    two_symbols = [f"{sid}.TWO" for sid in df_valid['stock_id']]

    print(f"📥 正在下載即時數據 (這需要一點時間)...")
    
    # 💡 關鍵：分兩大批下載，避免 yfinance 下載錯誤
    # 使用 multi_level_index=False 簡化表格結構
    data_tw = yf.download(tw_symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)
    data_two = yf.download(two_symbols, period="2d", interval="1d", group_by='ticker', progress=False, threads=True)

    hits = []
    
    for sid in df_valid['stock_id']:
        if sid in sent_list: continue
        
        # 嘗試從上市數據或上櫃數據中抓取資料
        ticker_tw = f"{sid}.TW"
        ticker_two = f"{sid}.TWO"
        
        df = pd.DataFrame()
        if ticker_tw in data_tw.columns.levels[0]:
            df = data_tw[ticker_tw]
        if (df.empty or df['Volume'].isnull().all()) and ticker_two in data_two.columns.levels[0]:
            df = data_two[ticker_two]
            
        if df.empty or len(df) < 2: continue
        
        try:
            # 取得昨日與今日數據
            y_vol = df['Volume'].iloc[-2]
            t_vol = df['Volume'].iloc[-1]
            t_high = df['High'].iloc[-1]
            t_close = df['Close'].iloc[-1]
            
            if pd.isna(y_vol) or y_vol == 0: continue

            # --- 核心邏輯判斷 ---
            vol_ratio = t_vol / y_vol
            drop_ratio = (t_high - t_close) / t_high if t_high > 0 else 0

            # 門檻：量增 1.5x 且 回落 4%
            if vol_ratio >= 1.5 and drop_ratio >= 0.04:
                hits.append({
                    'id': sid, 
                    'name': name_dict.get(sid, "未知"), 
                    'price': t_close, 
                    'high': t_high, 
                    'drop': round(drop_ratio * 100, 1), 
                    'vol_x': round(vol_ratio, 1)
                })
                sent_list.add(sid)
        except: continue

    # 3. 發送報告
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚠️ 【全市場爆量上引線警報】\n⏰ {datetime.now().strftime('%m/%d %H:%M')}\n門檻: 量增 1.5x / 回落 4%\n"
        msg += "─" * 15 + "\n"
        for h in hits[:15]:
            msg += f"🔹 {h['id']} {h['name']}\n"
            msg += f"   💰 現價:{h['price']:.2f} (高點:{h['high']:.2f})\n"
            msg += f"   📉 高點回落:{h['drop']}% | 🔥量增:{h['vol_x']}倍\n"
            msg += f"   🔗 https://tw.tradingview.com/chart/?symbol=TWSE:{h['id']}\n"
            msg += "─" * 10 + "\n"
        
        send_alert(msg)
        save_sent_list(sent_list)
        print(f"✅ 成功發送警報，命中 {len(hits)} 檔標的。")
    else:
        print("ℹ️ 掃描完畢，目前市場無符合標的。")

if __name__ == "__main__":
    main()
