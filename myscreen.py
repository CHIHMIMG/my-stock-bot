import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# ==================== 設定區 ====================
# 1. 填入你 image_d0c751 那串正確的 Token
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='

# 2. 填入接收者的 User ID (可放入多人，用逗號隔開)
# 你的 ID：U8b817b96fca9ea9a0f22060544a01573
LINE_USER_IDS = [
    'U8b817b96fca9ea9a0f22060544a01573',
    '這裡填入朋友A的UID',
    '這裡填入朋友B的UID'
]
# ===============================================

def send_line(msg):
    """使用 Multicast 接口一次發給所有人"""
    url = 'https://api.line.me/v2/bot/message/multicast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_IDS,
        'messages': [{'type': 'text', 'text': msg}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            print(f"✅ 成功發送給 {len(LINE_USER_IDS)} 人")
        else:
            print(f"❌ 發送失敗，狀態碼：{response.status_code}")
    except Exception as e:
        print(f"⚠️ 錯誤：{e}")

def screen_stocks():
    """你的選股邏輯"""
    # 這裡可以放你原本 yfinance 的抓取清單
    target_stocks = ['2330.TW', '2303.TW', '2454.TW'] 
    results = []
    
    for stock_id in target_stocks:
        stock = yf.Ticker(stock_id)
        # 簡單示範：獲取今日收盤價
        data = stock.history(period='1d')
        if not data.empty:
            price = data['Close'].iloc[-1]
            results.append(f"{stock_id}: {price:.2f}")

    today = datetime.now().strftime('%Y-%m-%d')
    if results:
        msg = f"📊 {today} 每日股價追蹤：\n" + "\n".join(results)
    else:
        msg = f"📊 {today} 無法取得股價資訊"
        
    send_line(msg)

if __name__ == "__main__":
    screen_stocks()
