import tkinter as tk
from tkinter import scrolledtext
import undetected_chromedriver as uc
import time
import urllib.parse as urlparse
from selenium.webdriver.common.by import By

# 全域變數：儲存當前的瀏覽器實例與 Session ID
active_driver = None
current_sid = ""

def auto_login_stealth():
    global active_driver, current_sid
    url = url_entry.get()
    
    log_display.insert(tk.END, "正在啟動隱形瀏覽器 (版本 143)...\n")
    log_display.update()

    try:
        options = uc.ChromeOptions()
        options.add_argument("--disable-popup-blocking") 
        
        # 初始化瀏覽器 (鎖定版本以避免衝突)
        active_driver = uc.Chrome(version_main=143, options=options, use_subprocess=True)
        active_driver.get(url)
        
        log_display.insert(tk.END, "進入網站，等待 Cloudflare 檢查...\n")
        time.sleep(6) 

        # 執行登入程序
        log_display.insert(tk.END, "輸入帳號密碼中...\n")
        active_driver.find_element(By.ID, "iuser").send_keys(user_entry.get())
        time.sleep(1)
        active_driver.find_element(By.ID, "ipswd").send_keys(pw_entry.get())
        time.sleep(1)
        active_driver.find_element(By.ID, "mybutton").click()
        
        log_display.insert(tk.END, "點擊登入，等待後台載入...\n")
        time.sleep(8) 
        
        # 提取初始 SID 並顯示所有 Cookie
        update_sid_info()
        log_display.insert(tk.END, "--- 登入成功並獲取憑證 ---\n")

    except Exception as e:
        log_display.insert(tk.END, f"發生錯誤: {str(e)}\n")

def update_sid_info():
    """從當前網址與 Cookie 中提取最新的 SID"""
    global current_sid
    if not active_driver:
        return

    # 1. 從網址提取 SID (對應 index.php 邏輯)
    parsed = urlparse.urlparse(active_driver.current_url)
    url_params = urlparse.parse_qs(parsed.query)
    if 'sid' in url_params:
        current_sid = url_params['sid'][0]
        log_display.insert(tk.END, f"[網址 SID] 提取成功: {current_sid}\n")

    # 2. 顯示關鍵 Cookie (不分大小寫)
    cookies = active_driver.get_cookies()
    for cookie in cookies:
        c_name = cookie['name'].lower()
        if "a168" in c_name or "sid" in c_name:
            log_display.insert(tk.END, f"[Cookie] {cookie['name']}: {cookie['value']}\n")

def execute_action(action_type):
    """模擬執行修改動作"""
    global current_sid
    if not active_driver:
        log_display.insert(tk.END, "請先執行登入！\n")
        return

    log_display.insert(tk.END, f"正在執行 {action_type} 格式修改程序...\n")
    
    # 根據你提供的 URL 構造請求
    # 既然網址一樣，程式會直接導向該修改頁面
    target_url = f"https://hp8.pokp02.net/index.php?ctrl=UserModify.php&sid={current_sid}&ulv=5&uid=54379&id=135697253&lv=7"
    
    active_driver.get(target_url)
    time.sleep(3) # 等待伺服器處理

    # 檢查 Response 內容 (對應你上傳的 index 10K/20K.php)
    page_source = active_driver.page_source
    if "modify success" in page_source or "修改完成" in page_source:
        log_display.insert(tk.END, "修改成功！伺服器已回傳成功腳本。\n")
        # 成功後 SID 可能會更新，再次提取
        update_sid_info()
    else:
        log_display.insert(tk.END, "未偵測到成功字樣，請檢查瀏覽器狀態。\n")

# --- GUI 介面 (修正佈局衝突) ---
root = tk.Tk()
root.title("自動修改與 Token 監控工具")
root.geometry("700x700")

# 登入區
frame_login = tk.LabelFrame(root, text="步驟 1: 帳號登入", padx=10, pady=10)
frame_login.pack(padx=10, pady=5, fill="x")

tk.Label(frame_login, text="網址:").grid(row=0, column=0, sticky="w")
url_entry = tk.Entry(frame_login, width=50)
url_entry.insert(0, "https://hp8.pokp02.net/")
url_entry.grid(row=0, column=1, pady=2)

tk.Label(frame_login, text="帳號:").grid(row=1, column=0, sticky="w")
user_entry = tk.Entry(frame_login, width=30)
user_entry.grid(row=1, column=1, sticky="w", pady=2)

tk.Label(frame_login, text="密碼:").grid(row=2, column=0, sticky="w")
pw_entry = tk.Entry(frame_login, width=30, show="*")
pw_entry.grid(row=2, column=1, sticky="w", pady=2)

btn_start = tk.Button(root, text="啟動登入並抓取 Cookie", command=auto_login_stealth, bg="blue", fg="white", font=("Arial", 10, "bold"))
btn_start.pack(pady=10)

# 修改執行區
frame_action = tk.LabelFrame(root, text="步驟 2: 修改操作", padx=10, pady=10)
frame_action.pack(padx=10, pady=5, fill="x")

tk.Button(frame_action, text="執行 10K 格式", command=lambda: execute_action("10K"), bg="#2E7D32", fg="white", width=15).grid(row=0, column=0, padx=20)
tk.Button(frame_action, text="執行 20K 格式", command=lambda: execute_action("20K"), bg="#E65100", fg="white", width=15).grid(row=0, column=1, padx=20)

# Log 顯示
log_display = scrolledtext.ScrolledText(root, width=85, height=25)
log_display.pack(padx=10, pady=10)

root.mainloop()