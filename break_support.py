import yfinance as yf
import requests
import os
import pandas as pd

DISCORD_WEBHOOK_URL = '你的_DISCORD_WEBHOOK_URL'

def check_breakthrough():
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]

    if not targets: return

    still_watching = set() # 使用 set 儲存還沒破的代號
    
    for sid in targets:
        try:
            df = yf.download(f"{sid}.TW", period="5d", progress=False, auto_adjust=False)
            if df.empty: df = yf.download(f"{sid}.TWO", period="5d", progress=False, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # 尋找最近 3 天內的爆量低點
            support_price = None
            for i in range(1, 4):
                if df['Volume'].iloc[-i] >= (df['Volume'].iloc[-i-1] * 2):
                    support_price = df['Low'].iloc[-i]
                    break
            
            current_price = df['Close'].iloc[-1]
            if support_price and current_price < support_price:
                # 報警，不加回 still_watching
                requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🚨 **跌破警報**：{sid} 現價 {current_price} 破大量支撐 {support_price:.2f}！"})
            else:
                still_watching.add(sid)
        except: 
            still_watching.add(sid)

    # 更新檔案
    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
