import yfinance as yf
import requests
import os
import pandas as pd

# --- 設定區 ---
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def check_breakthrough():
    if not os.path.exists('targets.txt'):
        print("找不到 targets.txt")
        return
        
    with open('targets.txt', 'r') as f:
        targets = [line.strip() for line in f.readlines() if line.strip()]

    if not targets:
        print("監控清單為空")
        return

    still_watching = []
    
    for sid in targets:
        try:
            # 抓取數據
            df = yf.download(f"{sid}.TW", period="5d", progress=False, auto_adjust=False)
            if df.empty: df = yf.download(f"{sid}.TWO", period="5d", progress=False, auto_adjust=False)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 尋找最近 3 天內的 2 倍爆量日低點
            support_price = None
            for i in range(1, 4):
                if len(df) < i+1: continue
                if df['Volume'].iloc[-i] >= (df['Volume'].iloc[-i-1] * 2):
                    support_price = df['Low'].iloc[-i]
                    break
            
            current_price = df['Close'].iloc[-1]
            if support_price and current_price < support_price:
                # 報警並移除
                requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🚨 **跌破警報**：{sid} 現價 {current_price} 破大量支撐 {support_price:.2f}！"})
            else:
                still_watching.append(sid)
        except Exception as e:
            print(f"處理 {sid} 出錯: {e}")
            still_watching.append(sid)

    with open('targets.txt', 'w') as f:
        f.write('\n'.join(still_watching))

if __name__ == "__main__":
    check_breakthrough()
