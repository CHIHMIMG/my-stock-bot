import requests

# ==================== 關鍵設定 ====================
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
# =================================================

def final_detect():
    headers = {'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'}
    
    print("\n" + "🎯" * 5 + " 最終群組清單掃描 " + "🎯" * 5)
    
    # 這個 API 會直接列出機器人加入的所有群組 ID
    # 注意：這僅限於「聊天機器人」模式下有效
    url = 'https://api.line.me/v2/bot/group/member/count/...' # 故意觸發清單
    
    # 真正的查詢：我們先嘗試獲取機器人的基本資訊，看有沒有帶出群組
    info_url = 'https://api.line.me/v2/bot/info'
    res = requests.get(info_url, headers=headers)
    
    print(f"🕵️ 機器人基本資訊: {res.text}")
    print("💡 如果上面沒看到 C 開頭 ID，請務必執行下方步驟！")
    print("🎯" * 5 + " 掃描結束 " + "🎯" * 5 + "\n")

if __name__ == "__main__":
    final_detect()
