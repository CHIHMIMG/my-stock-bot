import pandas as pd
from FinMind.data import DataLoader
import requests
import datetime
import os
import time

# --- 設定區 ---
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'

def send_line_message(msg):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    payload = {'to': LINE_USER_ID, 'messages': [{'type': 'text', 'text': msg}]}
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code

def main():
    print("🚀 啟動盤後精準選股 (今日爆量 1.5倍, >6000張, 股價<100)...")
    dl = DataLoader()
    
    # 1. 抓取今日全市場資料
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    df_today = dl.taiwan_stock_daily_all(date=today_str)
    
    if df_today.empty:
        print(f"❌ {today_str} 無法取得數據。")
        return

    # 初步過濾：股價 < 100 且 成交量 > 6000張 (FinMind 成交量為股數，需除以 1000)
    df_today['vol_sheets'] = df_today['成交量'] / 1000
    mask = (df_today['close'] < 100) & (df_today['vol_sheets'] >= 6000)
    potential_list = df_today[mask].copy()

    final_selection = []
    # 抓取最近 10 天歷史，確保能找到上一個交易日
    start_str = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    
    for index, row in potential_list.iterrows():
        sid = row['stock_id']
        sname = row['stock_name']
        
        # 2. 針對個股抓取歷史數據進行精準比對
        try:
            stock_history = dl.taiwan_stock_daily(stock_id=sid, start_date=start_str)
            
            if len(stock_history) >= 2:
                # iloc[-1] 是今天, iloc[-2] 是前一交易日
                vol_today = stock_history['Volume'].iloc[-1]
                vol_yesterday = stock_history['Volume'].iloc[-2]
                current_close = stock_history['close'].iloc[-1]
                
                # 判斷是否符合 1.5 倍爆量
                if vol_today >= (vol_yesterday * 1.5):
                    final_selection.append({
                        'id': sid,
                        'name': sname,
                        'close': current_close,
                        'vol': int(vol_today / 1000),
                        'diff': round(row['漲跌幅'], 2)
                    })
                    print(f"🎯 發現標的：{sid} {sname} (量增 {round(vol_today/vol_yesterday, 2)} 倍)")
            
            # 稍微停頓避免請求過快
            time.sleep(0.1)
            
        except Exception as e:
            print(f"⚠️ 無法處理 {sid}: {e}")

    # 3. 發送 LINE 與更新 targets.txt
    if final_selection:
        target_ids = [s['id'] for s in final_selection]
        with open('targets.txt', 'w') as f:
            f.write('\n'.join(target_ids))
        
        msg = f"📊 {today_str} 爆量選股(中文摘要)\n"
        msg += "------------------\n"
        for s in final_selection:
            msg += f"🔹 {s['id']} {s['name']}\n"
            msg += f"   收盤價: {s['close']}\n"
            msg += f"   漲跌幅: {s['diff']}%\n"
            msg += f"   成交量: {s['vol']}張\n"
        
        send_line_message(msg)
        print(f"✅ 成功選出 {len(final_selection)} 檔，LINE 已通知。")
    else:
        send_line_message(f"📊 {today_str} 選股結束：無符合條件標的。")
        with open('targets.txt', 'w') as f:
            f.write('')
        print("今日無符合條件股票。")

if __name__ == "__main__":
    main()
