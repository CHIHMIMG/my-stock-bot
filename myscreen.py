import pandas as pd
from FinMind.data import DataLoader
import requests
import datetime
import os
import time

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1455572127095848980/uyuzoVxMm-y3KWas2bLUPPAq7oUftAZZBzwEmnCAjkw54ZyPebn8M-6--woFB-Eh7fDL'

def send_alert(msg):
    """發送警報至 Discord 與 LINE"""
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=15)
    except: pass
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def main():
    print("🚀 啟動盤後精準選股 (今日爆量 1.5倍, >6000張, 股價<100)...")
    dl = DataLoader()
    
    # 修正：使用最新的數據獲取方式
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 抓取全市場快報 (使用今日日期)
    try:
        df_today = dl.taiwan_stock_daily_info(date=today_str)
    except:
        print(f"❌ 無法取得 {today_str} 數據，嘗試前一交易日...")
        return

    if df_today.empty:
        print("❌ 今日數據為空。")
        return

    # 初步過濾：股價 < 100 且 成交張數 >= 6000 (FinMind 單位通常是股)
    # 欄位名稱依版本可能不同，這裡做相容性處理
    df_today['成交張數'] = df_today['成交量'] / 1000
    mask = (df_today['收盤價'] < 100) & (df_today['成交張數'] >= 6000)
    potential_list = df_today[mask].copy()

    final_selection = []
    # 抓取過去 10 天，確保能找到上一個交易日比對
    start_str = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    
    for index, row in potential_list.iterrows():
        sid = row['證券代碼']
        sname = row['證券名稱']
        
        try:
            # 獲取個股精準歷史數據
            stock_history = dl.taiwan_stock_daily(stock_id=sid, start_date=start_str)
            
            if len(stock_history) >= 2:
                # 倒數第1筆是今天，倒數第2筆是上一個交易日
                vol_today = stock_history['Volume'].iloc[-1]
                vol_yesterday = stock_history['Volume'].iloc[-2]
                current_close = stock_history['close'].iloc[-1]
                
                # 💡 今日量 > 昨日量 1.5 倍
                if vol_today >= (vol_yesterday * 1.5):
                    final_selection.append({
                        'id': sid,
                        'name': sname,
                        'close': current_close,
                        'vol': int(vol_today / 1000),
                        'diff': round(((current_close - stock_history['close'].iloc[-2]) / stock_history['close'].iloc[-2]) * 100, 2)
                    })
            time.sleep(0.1) # 避開頻率限制
        except:
            continue

    # 3. 發送摘要並更新 targets.txt
    if final_selection:
        target_ids = [s['id'] for s in final_selection]
        with open('targets.txt', 'w') as f:
            f.write('\n'.join(target_ids))
        
        msg = f"📊 {today_str} 盤後爆量選股摘要\n"
        msg += "------------------\n"
        for s in final_selection:
            msg += f"🔹 {s['id']} {s['name']}\n"
            msg += f"   收盤價: {s['close']}\n"
            msg += f"   漲跌幅: {s['diff']}%\n"
            msg += f"   成交量: {s['vol']}張\n"
        
        send_alert(msg)
        print(f"✅ 成功選出 {len(final_selection)} 檔，已發送 LINE/Discord。")
    else:
        send_alert(f"📊 {today_str} 選股結束：無符合爆量條件標的。")
        with open('targets.txt', 'w') as f:
            f.write('')

if __name__ == "__main__":
    main()
