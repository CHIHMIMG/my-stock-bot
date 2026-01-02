import requests
import json

# ==================== 關鍵設定區 ====================
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU=' # 圖 image_d0c751 那串
MY_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ====================================================

def capture_id():
    headers = {
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("\n" + "🔍" * 5 + " 開始全面搜捕 ID " + "🔍" * 5)
    
    # 方法 A：發送測試訊息並印出完整 Response
    push_url = 'https://api.line.me/v2/bot/message/push'
    payload = {'to': MY_USER_ID, 'messages': [{'type': 'text', 'text': '正在抓取 ID...'}]}
    res = requests.post(push_url, headers=headers, json=payload)
    print(f"【推播測試回覆】: {res.text}")

    # 方法 B：檢查機器人所在的群組總數 (這有時會帶出隱藏資訊)
    # 這裡我們利用一個小技巧，故意發給一個不存在的 C ID，看錯誤訊息是否會提示正確格式
    test_group_url = 'https://api.line.me/v2/bot/message/push'
    wrong_payload = {'to': 'C00000000000000000000000000000000', 'messages': [{'type': 'text', 'text': 'ID?'}]}
    res_err = requests.post(test_group_url, headers=headers, json=wrong_payload)
    print(f"【群組連線偵測】: {res_err.text}")

    print("🔍" * 5 + " 搜捕結束，請查看上方內容 " + "🔍" * 5 + "\n")

if __name__ == "__main__":
    capture_id()
