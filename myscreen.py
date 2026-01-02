import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# ==================== 偵探模式設定區 ====================
# 1. 填入你的 Channel Access Token
LINE_ACCESS_TOKEN = ''ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU=''

# 2. 填入你自己的 User ID (U8b817...那個)
# 這樣偵探結果才會私訊發給你
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ======================================================

def send_line(msg):
    """
    偵探模式專用發送函數
    會同時發送訊息並在 GitHub Log 印出所有隱藏資訊
    """
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': msg}]
    }
    
    try:
        # 執行發送
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        # --- 偵探重點：把所有回傳細節印出來 ---
        print("\n" + "="*50)
        print("🕵️ 偵探模式執行結果：")
        print(f"HTTP 狀態碼: {response.status_code}")
        print(f"LINE 伺服器回傳內容: {response.text}")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"⚠️ 偵探執行錯誤: {e}")

def get_group_id_detect():
    """
    主程式：發送一則測試訊息觸發日誌紀錄
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_msg = f"偵探模式啟動！\n執行時間：{now}\n請去 GitHub Actions 查看 Log。"
    
    # 執行發送
    send_line(test_msg)

if __name__ == "__main__":
    get_group_id_detect()
