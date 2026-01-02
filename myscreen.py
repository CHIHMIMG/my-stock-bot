def send_line(msg):
    import requests
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    # 這裡可以嘗試填入你猜測的 ID，但我們先維持發給你自己
    payload = {
        'to': 'U8b817b96fca9ea9a0f22060544a01573', 
        'messages': [{'type': 'text', 'text': msg}]
    }
    
    # 執行一次發送來確認連線
    response = requests.post(url, headers=headers, json=payload)
    print(f"🕵️ 目前連線正常: {response.status_code}")

    # --- 關鍵：嘗試抓取伺服器的互動資訊 ---
    # 因為你沒有架伺服器，我們試著去抓 LINE 的 Quota 資訊，有時會帶出所在群組數
    quota_url = 'https://api.line.me/v2/bot/message/quota/consumption'
    q_res = requests.get(quota_url, headers=headers)
    print(f"📊 本月訊息消耗量: {q_res.text}")
