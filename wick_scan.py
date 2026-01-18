import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
from FinMind.data import DataLoader
import os

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'
CACHE_FILE = 'sent_wick_spikes.txt'

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=10)
    except: pass

def main():
    print(f"🚀 啟動【盤中精準狙擊】: {datetime.now().strftime('%H:%M')}")
    dl = DataLoader()
    
    # 1. 取得最新市場清單與名單
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')
        # 先抓 FinMind 盤中概況作為「名單過濾器」
        df_today = dl.taiwan_stock_daily_prev_views(date=today_str)
        # 過濾：成交量 > 3000 且 股價 > 20
        fast_list = df_today[(df_today['vol'] >= 3000) & (df_today['close'] >= 20)]['stock_id'].tolist()
        
        stock_info = dl.taiwan_stock_info()
        valid_info = stock_info[(stock_info['stock_id'].isin(fast_list)) & (~stock_info['industry_category'].str.contains('金融'))]
        target_ids = valid_info['stock_id'].tolist()
        name_dict = dict(zip(valid_info['stock_id'], valid_info['stock_name']))
    except:
        return

    if not target_ids: return

    # 2. 抓取 YFinance 即時數據 (核心準確度來源)
    tickers = [f"{sid}.TW" for sid in target_ids] + [f"{sid}.TWO" for sid in target_ids]
    # 使用 auto_adjust=True 確保價格經過除權息修正，計算回落才準
    data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False, threads=True, auto_adjust=True)
    
    sent_list = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            sent_list = set(line.strip() for line in f.readlines())

    hits = []
    for sid in target_ids:
        if sid in sent_list: continue
        
        # 自動識別後綴
        ticker = f"{sid}.TW"
        if ticker not in data.columns.levels[0] or data[ticker].dropna().empty:
            ticker = f"{sid}.TWO"
        if ticker not in data.columns.levels[0]: continue
        
        # 取得數據表並去除空值
        df = data[ticker].dropna()
        if len(df) < 2: continue
        
        # 💡 確保數據為最新交易日
        # t = 今天, y = 昨天
        t_vol = float(df['Volume'].iloc[-1])   # 當下成交量
        y_vol = float(df['Volume'].iloc[-2])   # 昨日總成交量
        t_high = float(df['High'].iloc[-1])    # 今日盤中最高價
        t_close = float(df['Close'].iloc[-1])  # 當下最新成交價
        
        # 3. 嚴格邏輯判斷
        # 量增率 (當下量 / 昨天總量)
        vol_ratio = t_vol / y_vol if y_vol > 0 else 0
        # 回落率 ( (最高 - 當下) / 最高 )
        drop_ratio = (t_high - t_close) / t_high if t_high > 0 else 0
        t_vol_lots = int(t_vol / 1000)

        # 執行條件：量增 1.5 倍 且 回落 4%
        if vol_ratio >= 1.5 and drop_ratio >= 0.04:
            hits.append({
                'id': sid, 'name': name_dict.get(sid, "未知"), 
                'price': t_close, 'high': t_high, 
                'vol': t_vol_lots, 'drop': round(drop_ratio * 100, 1), 'vol_x': round(vol_ratio, 1)
            })
            sent_list.add(sid)

    # 4. 輸出與通知
    if hits:
        hits = sorted(hits, key=lambda x: x['drop'], reverse=True)
        msg = f"⚡ **【5分鐘即時狙擊】數據已確認**\n篩選: 量>3000 / 增>1.5x / 回落>4%\n"
        for h in hits[:10]:
            msg += f"📌 **{h['id']} {h['name']}**\n   現價: `{h['price']:.2f}` | 📉 **回落: {h['drop']}%**\n   成交: `{h['vol']}張` (量增: {h['vol_x']}x)\n"
        send_discord(msg)
        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(list(sent_list)))
