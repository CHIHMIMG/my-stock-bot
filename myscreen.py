import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import requests
import datetime

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'
VOL_THRESHOLD = 6000  # 成交量大於 6000 張
VOL_RATIO = 2.0       # 量增 2 倍以上

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=20)
    except:
        pass

def screen_stocks():
    report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 啟動掃描 (去重模式)... {report_time}")
    
    dl = DataLoader()
    stock_info = dl.taiwan_stock_info()
    
    # 確保原始名單不重複
    raw_list = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    unique_list = []
    seen_sids = set()
    for sid, name in raw_list:
        if sid not in seen_sids:
            unique_list.append((sid, name))
            seen_sids.add(sid)
    
    hits_msgs = []
    hits_sids = set() # 使用 set 儲存命中代號，物理性防重複
    
    for sid, name in unique_list:
        try:
            df = yf.download(f"{sid}.TW", period="90d", progress=False, auto_adjust=False)
            if df.empty or len(df) < 61:
                df = yf.download(f"{sid}.TWO", period="90d", progress=False, auto_adjust=False)
            
            if df.empty or len(df) < 61: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            today_vol = float(df['Volume'].iloc[-1]) / 1000
            yesterday_vol = float(df['Volume'].iloc[-2]) / 1000
            close_price = float(df['Close'].iloc[-1])
            yesterday_close = float(df['Close'].iloc[-2])

            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            ma60 = df['Close'].rolling(60).mean().iloc[-1]

            if today_vol >= VOL_THRESHOLD and today_vol >= (yesterday_vol * VOL_RATIO) and close_price >= max(ma5, ma10, ma20, ma60):
                if sid in hits_sids: continue
                
                price_diff = close_price - yesterday_close
                p_percent = (price_diff / yesterday_close) * 100
                icon = "🔴" if price_diff > 0 else "🟢" if price_diff < 0 else "🟡"
                
                growth = round(today_vol / yesterday_vol, 2)
                res = f"{icon} **{sid} {name}**: `{round(close_price, 2)}` ({p_percent:+.2f}%) | 量:{int(today_vol)}張 ({growth}x)"
                hits_msgs.append(res)
                hits_sids.add(sid) 
        except:
            continue
            
    # 寫入檔案：使用 'w' 模式確保每次都是全新覆蓋
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(hits_sids))))
    
    if hits_msgs:
        header = f"📊 **【全台股 2.0倍量增名單】** (去重完畢)\n⏰ 時間：{report_time}\n"
        send_discord(header)
        for i in range(0, len(hits_msgs), 10):
            send_discord("\n".join(hits_msgs[i:i + 10]))
    else:
        send_discord(f"📊 掃描完成 ({report_time})，今日無符合標的。")

if __name__ == "__main__":
    screen_stocks()
