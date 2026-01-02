import requests

# ==================== 設定區 ====================
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
MY_USER_ID = 'U8b817b96fca9ea9a0f22060544a01573'
# ===============================================

def find_my_group():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    
    # 這是我們要發出的訊息
    msg_body = {
        'to': MY_USER_ID,
        'messages': [{'type': 'text', 'text': '正在執行 ID 深度掃描...'}]
    }

    # 重點：讓機器人發一則訊息給自己，並在 Log 印出「所有」回傳標頭
    response = requests.post('https://api.line.me/v2/bot/message/push', 
                             headers=headers, json=msg_body)
    
    print("\n" + "🏁" * 5 + " 最終捕捉日誌 " + "🏁" * 5)
    print(f"【狀態碼】: {response.status_code}")
    print(f"【伺服器完整回覆】: {response.text}")
    
    # 嘗試獲取機器人加入的群組數量
    count_res = requests.get('https://api.line.me/v2/bot/info', headers=headers)
    print(f"【機器人身分證】: {count_res.text}")
    print("🏁" * 5 + " 結束 " + "🏁" * 5 + "\n")

if __name__ == "__main__":
    find_my_group()
