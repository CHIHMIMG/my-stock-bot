import requests
import json

# ==================== 設定區 ====================
LINE_ACCESS_TOKEN = 'ODDI4pyqjUMem+HvWIj3MtiWZ6wxpnU43avaxvIX3d0slVswYKayOk3lBmuM5zeF6umMABnbJho5RK3+4GrERAxIbVQvYUJtNQ9c45gS8FzNR8/YqbKD4Fdyx+G4gHfdGrQmTSK2X9QhYLQhkHyyPgdB04t89/1O/w1cDnyilFU='
# ===============================================

def capture_id_deep_scan():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    
    print("\n" + "📡" * 5 + " 深度掃描啟動 " + "📡" * 5)
    
    # 這裡我們利用 get_bot_info 接口，有時候它會回傳機器人最後互動的群組
    info_url = 'https://api.line.me/v2/bot/info'
    info_res = requests.get(info_url, headers=headers)
    print(f"【機器人基本資料】: {info_res.text}")
    
    # 強迫觸發一個錯誤回報，看錯誤訊息是否帶出所在地
    err_url = 'https://api.line.me/v2/bot/message/push'
    err_payload = {'to': 'C00000000000000000000000000000000', 'messages': [{'type': 'text', 'text': 'ID'}]}
    err_res = requests.post(err_url, headers=headers, json=err_payload)
    print(f"【系統回報資訊】: {err_res.text}")

    print("\n💡 請確認 Webhook 已開啟，並在群組隨便標記一下機器人！")
    print("📡" * 5 + " 掃描結束 " + "📡" * 5 + "\n")

if __name__ == "__main__":
    capture_id_deep_scan()
