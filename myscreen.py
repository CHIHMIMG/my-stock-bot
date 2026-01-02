import requests
import json
from datetime import datetime

# ==================== 關鍵設定區 ====================
# 1. 請填入圖 image_d0c751.png 那串完整的 Token (記得前後單引號)
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='

# 2. 填入你自己的 User ID (U8b817...那個) 用來驗證連線
MY_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ====================================================

def send_line(msg):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'to': MY_USER_ID,
        'messages': [{'type': 'text', 'text': msg}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        # --- 這裡是你要找的答案區 ---
        print("\n" + "🔍" * 10 + " 偵探日誌開始 " + "🔍" * 10)
        print(f"【連線狀態】: {response.status_code}")
        print(f"【伺服器回覆內容】: {response.text}")
        
        # 嘗試從回覆中解析潛在的 ID 資訊
        if response.status_code == 200:
            print("✅ 成功連線！Token 已修正。")
            print("💡 提示：如果機器人已在群組，請去 LINE Developers 開啟 Webhook 並點擊 Verify")
        elif response.status_code == 401:
            print("❌ 狀態 401：Token 還是不對！請檢查是否有空格或少複製結尾的 = 號。")
        
        print("🔍" * 10 + " 偵探日誌結束 " + "🔍" * 10 + "\n")
        
    except Exception as e:
        print(f"⚠️ 發生錯誤: {e}")

if __name__ == "__main__":
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    send_line(f"ID 捕獲測試中\n時間：{now}")
