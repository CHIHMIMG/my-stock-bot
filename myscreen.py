import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

# 預設一些熱門觀察股代碼 (你可以手動增加更多)
MONITOR_LIST = ['2330','2303','6116','2369','3060','3576','4919','2419','2630','2340','2349','6126','6016','3027','6026','6005','6244','6190','8074','8105','8422']

def send_alert(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
    except: pass
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def get_stock_name(symbol):
    # 這裡可以透過簡單的字典對應，或直接回傳代號
    return f"台股 {symbol}"

def main():
    print(f"🚀 啟動 yfinance 版精準選股: {datetime.now().strftime('%Y-%m-%d')}")
    
    final_selection = []
    
    # 這裡我們直接遍歷你的 targets 名單，或者你可以放一個更廣的名單
    # 如果你要全市場掃描，yfinance 速度會慢，建議先放你關注的 50-100 檔
    for sid in MONITOR_LIST:
        try:
            ticker = yf.Ticker(f"{sid}.TW")
            df = ticker.history(period="5d")
            if df.empty:
                ticker = yf.Ticker(f"{sid}.TWO")
                df = ticker.history(period="5d")
            
            if len(df) < 2: continue
            
            # 數據提取
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            price = today['Close']
            vol_today = today['Volume'] / 1000 # 換算成張
            vol_yesterday = yesterday['Volume'] / 1000
            
            # 條件判斷
            if price < 100 and vol_today > 6000 and vol_today >= (vol_yesterday * 1.5):
                change = ((price - yesterday['Close']) / yesterday['Close']) * 100
                final_selection.append({
                    'id': sid,
                    'price': round(price, 2),
                    'vol': int(vol_today),
                    'diff': round(change, 2)
                })
                print(f"✅ 發現標的: {sid} (量增 {round(vol_today/vol_yesterday, 2)}倍)")
        except:
            continue

    if final_selection:
        target_ids = [s['id'] for s in final_selection]
        with open('targets.txt', 'w') as f:
            f.write('\n'.join(target_ids))
        
        msg = f"📊 {datetime.now().strftime('%m/%d')} 盤後爆量選股\n"
        msg += "------------------\n"
        for s in final_selection:
            msg += f"🔹 {s['id']}\n"
            msg += f"   收盤價: {s['price']}\n"
            msg += f"   漲跌幅: {s['diff']}%\n"
            msg += f"   成交量: {s['vol']}張\n"
        
        send_alert(msg)
        print(f"✅ 成功選出 {len(final_selection)} 檔標的")
    else:
        print("今日無符合條件標的。")

if __name__ == "__main__":
    main()
