import requests

# ==================== 關鍵設定 ====================
# 1. 填入你 image_d0c751 那串 Token
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='

# 2. 這裡不填 ID，我們改用廣播模式
# =================================================

def broadcast_to_all(msg):
    """
    廣播模式：這會發送訊息給「所有」加過機器人好友的人。
    只要群組裡的人有加過它，通常群組也會收到通知。
    """
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        'messages': [{'type': 'text', 'text': msg}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        print(f"🕵️ 廣播結果：{response.status_code}")
        print(f"🕵️ 回覆內容：{response.text}")
    except Exception as e:
        print(f"⚠️ 發生錯誤：{e}")

if __name__ == "__main__":
    test_msg = "🚨 股票機器人連線成功！\n如果你看到這則訊息，代表我已經找到你了！"
    broadcast_to_all(test_msg)
