import requests
import pandas as pd

# 1. 設定目標 URL 與 Header (包含你的 Token)
url = "https://wpapi.ldjzmr.top/master/brand"
params = {
    "name": "",
    "contacts": "",
    "phone": "",
    "username": "",
    "remark": "",
    "page": 1,
    "page_size": 5000  # 你可以根據需要調整抓取的數量
}

headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3dwYXBpLmxkanptci50b3AvbWFzdGVyL2xvZ2luIiwiaWF0IjoxNzY5NjkzNjQ5LCJleHAiOjE4MDEyMjk2NDksIm5iZiI6MTc2OTY5MzY0OSwianRpIjoiNUVXTEFqeFRHTDlNRnc2QiIsInN1YiI6IjEzIiwicHJ2IjoiMTg4ODk5NDM5MDUwZTVmMzc0MDliMThjYzZhNDk1NjkyMmE3YWIxYiJ9.iyBmiRm5QiZxoOtvWVoRVyDyR4c-V9DmOH6_ztrlNNY",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    # 2. 發送請求
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # 檢查請求是否成功
    
    data_json = response.json()
    
    # 3. 解析數據 (根據一般後台 API 結構，數據通常在 'data' 或 'list' 欄位中)
    # 請根據實際 API 返回的結構調整路徑，這裡假設是在 ['data']['data'] 或 ['data']['list']
    items = data_json.get('data', {}).get('data', []) 
    
    if not items:
        print("未抓取到數據，請檢查 API 返回結構或 Token 是否過期。")
    else:
        # 4. 轉換成 DataFrame
        df = pd.DataFrame(items)
        
        # 5. 繁體中文欄位對應 (根據圖片調整)
        column_mapping = {
            "id": "ID",
            "name": "商戶名稱",
            "machine_count": "機器數量",
            "area": "商戶地域",
            "agent": "所屬代理",
            "contacts": "聯繫人",
            "username": "登錄賬號",
            "ratio": "分成[%]",
            "min_open_amount": "單次開分金額",
            "min_wash_amount": "最低洗分金額",
            "total_in": "投鈔",
            "total_open": "開分",
            "total_wash": "洗分",
            "profit": "盈餘",
            "created_at": "創建時間",
            "remark": "備註",
            "balance": "餘額"
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 6. 導出成 Excel
        output_file = "商戶列表數據.xlsx"
        df.to_excel(output_file, index=False)
        print(f"成功！數據已儲存至: {output_file}")

except Exception as e:
    print(f"發生錯誤: {e}")