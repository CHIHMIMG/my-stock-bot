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
    print("🚀 啟動盤後精準選股 (自動尋找最近交易日)...")
    dl = DataLoader()
    
    # 自動尋找最近有數據的日期 (往回找 5 天)
    df_today = pd.DataFrame()
    target_date = datetime.datetime.now()
    
    for _ in range(5):
        date_str = target_date.strftime('%Y-%m-%d')
        try:
            # 使用最新的 daily_info 介面
            df_today = dl.taiwan_stock_daily_info(date=date_str)
            if not df_today.empty:
                print(f"✅ 成功取得 {date_str} 數據")
                break
        except:
            pass
        target_date -= datetime.timedelta(days=1)
        print(f"🔎 {date_str} 無數據，嘗試前一天...")

    if df_today.empty:
        print("❌ 搜尋範圍內皆無數據。")
        return

    # 條件過濾：股價 < 100 且 成交張數 >= 6000
    df_today['成交張數'] = df_today['成交量'] / 1000
    mask = (df_today['收盤價'] < 100) & (df_today['成交張數'] >= 6000)
    potential_list = df_today[mask].copy()

    final_selection = []
    # 抓取歷史數據用於比對爆量 (回溯 15 天)
    history_start = (target_date - datetime.timedelta(days=15)).strftime('%Y-%m-%d')
    
    for index, row in potential_list.iterrows():
        sid = row['證券代碼']
        sname = row['證券名稱']
        
        try:
            # 精準獲取個股歷史
            stock_history = dl.taiwan_stock_daily(stock_id=sid, start_date=history_start)
            
            if len(stock_history) >= 2:
                # 最後一筆為當日，倒數第二筆為昨日
                vol_today = stock_history['Volume'].iloc[-1]
                vol_yesterday = stock_history['Volume'].iloc[-2]
                current_close = stock_history['close'].iloc[-1]
                
                # 今日量 > 昨日量 1.5 倍
                if vol_today >= (vol_yesterday * 1.5):
                    # 計算漲跌幅
                    prev_close = stock_history['close'].iloc[-2]
                    diff_pct = round(((current_close - prev_close) / prev_close) * 100, 2)
                    
                    final_selection.append({
                        'id': sid,
                        'name': sname,
                        'close': current_close,
                        'vol': int(vol_today / 1000),
                        'diff': diff_pct
                    })
            time.sleep(0.05) # 輕微停頓
        except:
            continue

    # 3. 發送摘要並更新 targets.txt
    if final_selection:
        # 按成交量排序
        final_selection = sorted(final_selection, key=lambda x: x['vol'], reverse=True)
        target_ids = [s['id'] for s in final_selection]
        
        with open('targets.txt', 'w') as f:
            f.write('\n'.join(target_ids))
        
        msg = f"📊 {target_date.strftime('%m/%d')} 盤後爆量精選\n"
        msg += "------------------\n"
        for s in final_selection:
            msg += f"🔹 {s['id']} {s['name']}\n"
            msg += f"   收盤價: {s['close']}\n"
            msg += f"   漲跌幅: {s['diff']}%\n"
            msg += f"   成交量: {s['vol']}張\n"
        
        send_alert(msg)
        print(f"✅ 成功選出 {len(final_selection)} 檔標的")
    else:
        print("今日無符合條件標的。")

if __name__ == "__main__":
    main()
