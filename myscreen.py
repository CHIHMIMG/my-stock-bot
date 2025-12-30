import pandas as pd
from FinMind.data import DataLoader
import datetime
import requestsDISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'
dl = DataLoader()

def send_discord(msg):
    data = {"content": msg}
    try:
        # Discord 的網址通常不會被封鎖
        r = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        return r.status_code
    except Exception as e:
        return f"傳送失敗: {e}"

def screen_stocks():
    print("🚀 啟動 Discord 模式篩選...")
    try:
        stock_info = dl.taiwan_stock_info()
        all_stocks = stock_info[stock_info['stock_id'].str.len() == 4][['stock_id', 'stock_name']].values.tolist()
    except:
        print("❌ 無法取得清單")
        return

    hits = []
    # 先測試前 20 檔就好，確認會響最重要
    for sid, name in all_stocks[:20]:
        try:
            df = dl.taiwan_stock_daily(stock_id=sid, start_date='2025-10-01')
            if df is None or len(df) < 20: continue
            
            today = df.iloc[-1]
            # 隨便設一個簡單條件測試：股價 > 10 元
            if today['close'] > 10:
                hits.append(f"✅ {sid} {name}: {today['close']}")
        except:
            continue
            
    # 執行發送
    report = "\n【今日選股測試】\n" + "\n".join(hits)
    status = send_discord(report)
    print(f"📢 Discord 發送狀態: {status}")

if __name__ == "__main__":
    screen_stocks()
