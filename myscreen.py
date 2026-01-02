import requests
from datetime import datetime

# ==================== 修正後的設定區 ====================
# 注意：Token 必須放在同一行，且前後都要有單引號 ' 
LINE_ACCESS_TOKEN = 'ODDl4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUjTNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/10/w1cDnyilFU='

# 填入你自己的 User ID (來自圖 image_c4890c.png)
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ======================================================

def send_line(msg):
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
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        # 這兩行是關鍵！會在 GitHub Actions 的 Log 裡印出資訊
        print(f"🕵️ 偵探回報 - 狀態碼: {response.status_code}")
        print(f"🕵️ 偵探回報 - 詳細內容: {response.text}")
    except Exception as e:
        print(f"⚠️ 偵探發生錯誤: {e}")

if __name__ == "__main__":
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    send_line(f"偵探模式測試中\n執行時間：{now}")
