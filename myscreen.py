import requests

# ==================== 修正後的設定區 ====================
# 1. 再次確認 Token 是否完整 (一定要 issue 新的試試看)
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='

# 2. 維持你個人的 User ID，用來驗證 Token 是否修好
MY_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ======================================================

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
        # --- 抓 ID 的關鍵日誌 ---
        print(f"🕵️ 偵探回報 - 狀態碼: {response.status_code}")
        print(f"🕵️ 偵探回報 - 詳細內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ Token 修好了！你可以收到私訊了。")
        elif response.status_code == 401:
            print("❌ Token 還是錯的，請確認是否複製到 Channel Secret 了？")
    except Exception as e:
        print(f"⚠️ 發生錯誤: {e}")

if __name__ == "__main__":
    send_line("偵探模式：正在驗證連線狀況...")
