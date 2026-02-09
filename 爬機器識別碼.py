import requests
import pandas as pd
import time

# 1. 設定
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3dwYXBpLmxkanptci50b3AvbWFzdGVyL2xvZ2luIiwiaWF0IjoxNzY5Mjg3NTQwLCJleHAiOjE4MDA4MjM1NDAsIm5iZiI6MTc2OTI4NzU0MCwianRpIjoiaXl6OWNaMjRGZGk3d0VrRCIsInN1YiI6IjExIiwicHJ2IjoiMTg4ODk5NDM5MDUwZTVmMzc0MDliMThjYzZhNDk1NjkyMmE3YWIxYiJ9.jUNFKexndLPuUqxYTf0TsUtF379rtD6HkF-zlHTZZxM"
API_URL = "https://wpapi.ldjzmr.top/master/machine"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def fetch_all_data():
    all_rows = []
    current_page = 1
    
    print("🚀 開始根據 JSON 結構爬取數據...")

    while True:
        # 根據回傳結構，參數應該用 'page'
        params = {"page": current_page}
        
        try:
            response = requests.get(API_URL, headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ 請求失敗，狀態碼：{response.status_code}")
                break
                
            res = response.json()
            
            # 定義資料提取路徑: res['data']['data']
            page_data = res.get('data', {}).get('data', [])
            
            if not page_data:
                print(f"🏁 第 {current_page} 頁沒有資料，停止抓取。")
                break

            for item in page_data:
                # 攤平巢狀結構 (Flatten nested JSON)
                row = {
                    "ID": item.get("id"),
                    "機台帳號": item.get("user", {}).get("phone"),  # user 物件裡的 phone
                    "機台狀態": item.get("user", {}).get("last_platform", "空閒"), # 參考截圖
                    "所屬商戶": item.get("brand", {}).get("name"),   # brand 物件裡的 name
                    "機器名稱": item.get("name"),
                    "連線狀態": "在線" if item.get("is_online") == 1 else "離線",
                    "機器標注": "正常", # 根據截圖顯示
                    "機器餘額": item.get("user", {}).get("score"),   # user 物件裡的 score
                    "機器唯一標識": item.get("machine_no"),
                    "當前版本": item.get("user", {}).get("version"), # user 物件裡的 version
                    "更新時間": item.get("updated_at")
                }
                all_rows.append(row)

            print(f"📦 已抓取第 {current_page} 頁，目前累計 {len(all_rows)} 筆數據")

            # 判斷是否還有下一頁 (根據 API 回傳的 next_page_url)
            if not res.get('data', {}).get('next_page_url'):
                print("✅ 已到達最後一頁。")
                break
            
            current_page += 1
            time.sleep(0.3) # 稍微停頓避免被封鎖

        except Exception as e:
            print(f"❌ 運行時發生錯誤: {e}")
            break

    # 存檔
    if all_rows:
        df = pd.DataFrame(all_rows)
        output_file = "機器管理列表_正式版.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\n✨ 處理完成！總共抓取 {len(all_rows)} 筆。")
        print(f"📁 檔案已儲存至: {output_file}")
    else:
        print("\n⚠️ 未抓取到任何有效數據。")

if __name__ == "__main__":
    fetch_all_data()