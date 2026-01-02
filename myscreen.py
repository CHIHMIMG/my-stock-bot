import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime

# --- 設定區 ---
# 請填入你的 LINE 或 Discord 資訊
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'

VOL_THRESHOLD = 6000  # 成交量門檻
VOL_RATIO = 1.5       # 【修改】量增 1.5 倍以上
PRICE_LIMIT = 100     # 【新增】股價上限 100 元

def send_line(msg):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': msg}]
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=20)
    except:
        pass

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動【1.5倍量 + 百元以下】掃描... {report_time}")
    
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    raw_list = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    
    unique_list = []
    seen_sids = set()
    for sid, name in raw_list:
        if sid not in seen_sids:
            unique_list.append((sid, name))
            seen_sids.add(sid)
    
    hits_msgs = []
    hits_sids = set()
    
    for sid, name in unique_list:
        try:
            df = yf.download(f"{sid}.TW", period="60d", progress=False, auto_adjust=False)
            if df.empty or len(df) < 10:
                df = yf.download(f"{sid}.TWO", period="60d", progress=False, auto_adjust=False)
            
            if df.empty or len(df) < 10: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            today_vol = float(df['Volume'].iloc[-1]) / 1000
            yesterday_vol = float(df['Volume'].iloc[-2]) / 1000
            close_price = float(df['Close'].iloc[-1])
            yesterday_close = float(df['Close'].iloc[-2])
            
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            # --- 判斷邏輯 ---
            # 1. 成交量 > 6000
            # 2. 今日量 > 昨日量 * 1.5
            # 3. 股價 <= 100 元 (【新增條件】)
            # 4. 股價站在所有均線上
            if (today_vol >= VOL_THRESHOLD and 
                today_vol >= (yesterday_vol * VOL_RATIO) and 
                close_price <= PRICE_LIMIT and 
                close_price >= max(ma5, ma10, ma20, ma60)):
                
                price_diff = close_price - yesterday_close
                p_percent = (price_diff / yesterday_close) * 100
                icon = "🔴" if price_diff > 0 else "🟢"
                
                growth = round(today_vol / yesterday_vol, 1)
                res = f"{icon} {sid} {name}: {round(close_price, 1)}元 ({p_percent:+.1f}%) 量:{int(today_vol)}張 ({growth}x)"
                hits_msgs.append(res)
                hits_sids.add(sid)
        except: continue
            
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(hits_sids))))
    
    if hits_msgs:
        full_msg = f"📊 【台股爆量名單 - 100元以下】\n⏰ {report_time}\n" + "\n".join(hits_msgs)
        send_line(full_msg)
    else:
        send_line(f"📊 掃描完成 ({report_time})，今日無符合標的。")

if __name__ == "__main__":
    screen_stocks()
