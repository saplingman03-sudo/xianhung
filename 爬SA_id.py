import requests
import pandas as pd # 如果沒有請執行 pip install pandas openpyxl

# 設定基礎資訊
base_url = "https://ldbapi.ledb.top/master/machine"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2xkYmFwaS5sZWRiLnRvcC9tYXN0ZXIvbG9naW4iLCJpYXQiOjE3NzAzOTYyNzAsImV4cCI6MTgwMTkzMjI3MCwibmJmIjoxNzcwMzk2MjcwLCJqdGkiOiJJVXhtR29lbzZlVVM5N2pSIiwic3ViIjoiMSIsInBydiI6IjE4ODg5OTQzOTA1MGU1ZjM3NDA5YjE4Y2M2YTQ5NTY5MjJhN2FiMWIifQ.uCGoZOMrMABWHf1pdzU-JioHiJ2cOUAa7bdwhF1C0x8"

headers = {
    "Authorization": f"Bearer {token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

all_results = []
page = 1
page_size = 50 # 稍微放大每頁數量提高效率

print("開始抓取所有機器資料...")

while True:
    params = {
        "pagenum": page,
        "pagesize": page_size
    }
    
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        res_data = response.json()
        
        # 根據你的 API 結構解析列表
        items = res_data.get('data', [])
        if isinstance(items, dict): # 處理分頁結構包裝
            items = items.get('data', [])
            
        if not items: # 如果這頁沒資料了就跳出迴圈
            break
            
        for item in items:
            # 提取 user 物件中的 SA_id
            user_info = item.get('user', {})
            all_results.append({
                "ID": item.get('id'),
                "機器編號": item.get('machine_no'),
                "SA_id": user_info.get('SA_id', "無資料"),
                "更新時間": user_info.get('updated_at')
            })
            
        print(f"第 {page} 頁抓取完成，目前累計 {len(all_results)} 筆。")
        page += 1
        
    except Exception as e:
        print(f"抓取第 {page} 頁時出錯: {e}")
        break

# 轉存 Excel
if all_results:
    df = pd.DataFrame(all_results)
    file_name = "所有機器SA_id列表.xlsx"
    df.to_excel(file_name, index=False)
    print(f"\n✅ 任務完成！共抓取 {len(all_results)} 筆資料。")
    print(f"檔案已儲存至: {file_name}")
else:
    print("❌ 未抓取到任何資料。")