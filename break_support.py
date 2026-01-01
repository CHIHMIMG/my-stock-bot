import yfinance as yf
import requests
import os
import pandas as pd

DISCORD_WEBHOOK_URL = https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def check_breakthrough():
    if not os.path.exists('targets.txt'): return
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]

    if not targets: return
    still_watching = set()
    
    for sid in targets:
        try:
            df = yf.download(f"{sid}.TW", period="10d", progress=False, auto_adjust=False)
            if df.empty: df = yf.download(f"{sid}.TWO", period="10d", progress=False, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # 【核心修改】尋找最近 4 天內的爆量支撐點
            support_price = None
            for i in range(1, 5): # 檢查回溯 4 天
                if df['Volume'].iloc[-i] >= (df['Volume'].iloc[-i-1] * 2):
                    support_price = df['Low'].iloc[-i]
                    break
            
            current_price = df['Close'].iloc[-1]
            if support_price and current_price < support_price:
                requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🚨 **跌破近4日天量支撐**：{sid}\n現價 {current_price} 破支撐 {support_price:.2f}！"})
            else:
                still_watching.add(sid)
        except: 
            still_watching.add(sid)

    with open('targets.txt', 'w') as f:
        f.write('\n'.join(sorted(list(still_watching))))

if __name__ == "__main__":
    check_breakthrough()
