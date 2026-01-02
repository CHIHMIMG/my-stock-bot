import requests

# ==================== 關鍵設定 ====================
# 1. 填入你 image_d0c751 那串 Token
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
# =================================================

def get_group_id_from_server():
    headers = {'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    
    print("\n" + "📡" * 5 + " 啟動終極掃描 " + "📡" * 5)
    
    # 這裡我們使用一個小技巧：檢查訊息剩餘量
    # 有時候 LINE 會在連線資訊中帶出機器人所在的群組屬性
    res = requests.get('https://api.line.me/v2/bot/message/quota/consumption', headers=headers)
    print(f"🕵️ 基礎掃描結果: {res.text}")

    print("\n💡【最重要步驟】請現在去 LINE 群組裡面：")
    print("1. 隨便標記一下機器人 (@股票機器人)")
    print("2. 在 LINE Developers 頁面點擊 Webhook 的 Verify 按鈕")
    print("3. 回到 GitHub Actions 重新執行一次，然後在下方黑色視窗按 Ctrl + F 搜尋 'C' 開頭代碼")
    print("📡" * 5 + " 掃描結束 " + "📡" * 5 + "\n")

if __name__ == "__main__":
    get_group_id_from_server()
