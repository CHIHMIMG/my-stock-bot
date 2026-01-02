import requests

# ==================== 正確填寫區 ====================
# 1. 這裡請直接貼上圖 image_d0c751.png 那串亂碼
# 注意：必須全部連在一起，前後各有一個單引號 '，中間不能有空格或斷行
LINE_ACCESS_TOKEN = 'ODDl4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUjTNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/10/w1cDnyilFU='

# 2. 維持你個人的 User ID (圖 image_c4890c.png)
LINE_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ===================================================

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
        # 這是我們要看的偵探結果！
        print(f"🕵️ 偵探回報 - 狀態碼: {response.status_code}")
        print(f"🕵️ 偵探回報 - 伺服器回覆: {response.text}")
        
        if response.status_code == 200:
            print("✅ 恭喜！Token 終於填對了，你的手機應該響了！")
    except Exception as e:
        print(f"⚠️ 偵探出錯: {e}")

if __name__ == "__main__":
    send_line("偵探模式：正在抓取 ID 資訊...")
