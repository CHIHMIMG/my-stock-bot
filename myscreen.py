import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

VOL_THRESHOLD = 6000  # 成交量門檻：6000張
VOL_RATIO = 1.5       # 量增倍數：1.5倍
PRICE_LIMIT = 100     # 股價門檻：100元以下

def send_notifications(msg):
    """發送通知到 Discord 與 LINE"""
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=20)
    except:
        pass
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=20)
    except:
        pass

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動掃描系統 | 條件: 近3日爆量(不含今日) | {report_time}")
    
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    # 排除金融股並過濾 4 位數代號
    filtered_info = stock_info[
        (stock_info['stock_id'].str.len() == 4) & 
        (~stock_info['industry_category'].str.contains('金融'))
    ]
    unique_list = filtered_info[['stock_id', 'stock_name']].drop_duplicates().values.tolist()
    
    hits_msgs = []
    hits_sids = set()
    
    for sid, name in unique_list:
        try:
            clean_sid = sid.strip()
            
            # 下載足夠長的數據 (取 70 天確保 MA60 與回溯邏輯正常)
            market_type = "TWSE"
            df = yf.download(f"{clean_sid}.TW", period="70d", progress=False, auto_adjust=False, multi_level_index=False)
            
            if df.empty or len(df) < 25:
                df = yf.download(f"{clean_sid}.TWO", period="70d", progress=False, auto_adjust=False, multi_level_index=False)
                market_type = "OTC"
            
            if df.empty or len(df) < 5: continue

            # --- 核心邏輯微調：不含假日的 3 個交易日 (不含當天) ---
            # df.iloc[-1] 是今天
            # df.iloc[-2] 是昨天 (第一個交易日)
            # df.iloc[-3] 是前天 (第二個交易日)
            # df.iloc[-4] 是大前天 (第三個交易日)
            
            past_3_days_data = df.iloc[-4:-1] # 取得昨天、前天、大前天這三列
            
            # 檢查這三天中是否有任何一天符合爆量條件
            is_hit = False
            hit_date_idx = -1
            
            for i in range(len(df)-4, len(df)-1):
                current_vol = df['Volume'].iloc[i]
                prev_vol = df['Volume'].iloc[i-1]
                current_price = df['Close'].iloc[i]
                
                # 計算均線 (針對該交易日計算)
                ma5 = df['Close'].rolling(5).mean().iloc[i]
                ma20 = df['Close'].rolling(20).mean().iloc[i]
                ma60 = df['Close'].rolling(60).mean().iloc[i]
                
                if (current_price <= PRICE_LIMIT and
                    current_vol / 1000 >= VOL_THRESHOLD and
                    current_vol >= (prev_vol * VOL_RATIO) and
                    current_price >= max(ma5, ma20, ma60)):
                    is_hit = True
                    hit_date_idx = i
                    break # 只要這三天有一點符合就選入
            
            if is_hit:
                target_data = df.iloc[hit_date_idx]
                prev_data = df.iloc[hit_date_idx-1]
                
                close_price = float(target_data['Close'])
                p_percent = ((close_price - float(prev_data['Close'])) / float(prev_data['Close'])) * 100
                today_vol = float(target_data['Volume']) / 1000
                growth = round(target_data['Volume'] / prev_data['Volume'], 1)
                hit_date = df.index[hit_date_idx].strftime('%m/%d')
                
                icon = "🔴" if p_percent > 0 else "🟢"
                tv_url = f"https://tw.tradingview.com/chart/?symbol={market_type}:{clean_sid}"
                
                res = (f"{icon} {clean_sid} {name}\n"
                       f"📅 爆量日: {hit_date}\n"
                       f"💰 股價: {close_price:.2f} ({p_percent:+.2f}%)\n"
                       f"📊 成交: {int(today_vol)}張 ({growth}x)\n"
                       f"🔗 線圖: {tv_url}\n")
                
                hits_msgs.append(res)
                hits_sids.add(clean_sid)

        except Exception:
            continue
            
    # 寫入監控名單
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(hits_sids))))
    
    if hits_msgs:
        header = f"🔥 【台股 3 日內爆量名單】\n(排除今日，不含假日)\n⏰ {report_time}\n" + "─" * 15 + "\n"
        for i in range(0, len(hits_msgs), 5):
            chunk = "\n".join(hits_msgs[i:i + 5])
            send_notifications(header + chunk if i == 0 else chunk)
    else:
        print("過去三個交易日無符合標的。")

if __name__ == "__main__":
    screen_stocks()
