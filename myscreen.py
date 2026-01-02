import requests
import json

# ==================== 設定區 ====================
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU=' # image_d0c751 裡的那串
# ===============================================

def capture_group_id():
    headers = {
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("\n" + "🔍" * 5 + " 正在掃描群組代號 " + "🔍" * 5)
    
    # 利用發送失敗的錯誤訊息來反查 ID 格式
    # 這是目前最有效的「暴力捕捉法」
    test_url = 'https://api.line.me/v2/bot/message/push'
    # 故意發給一個不存在的 C ID
    payload = {'to': 'C00000000000000000000000000000000', 'messages': [{'type': 'text', 'text': 'ID?'}]}
    response = requests.post(test_url, headers=headers, json=payload)
    
    print(f"🕵️ 捕捉日誌：{response.text}")
    print("🔍" * 5 + " 掃描結束 " + "🔍" * 5 + "\n")

if __name__ == "__main__":
    capture_group_id()
