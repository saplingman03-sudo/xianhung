#還要測試抓取cookie
import tkinter as tk
from tkinter import scrolledtext
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def auto_login():
    url = url_entry.get()
    username = user_entry.get()
    password = pw_entry.get()
    
    if not username or not password:
        log_display.insert(tk.END, "請先輸入帳號密碼！\n")
        return

    log_display.insert(tk.END, "正在啟動自動登入程序...\n")
    
    # 初始化瀏覽器
    options = webdriver.ChromeOptions()
    # 增加指紋模擬，減少被 Cloudflare 阻擋的機率
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(3) # 等待頁面與 Cloudflare 檢查加載

        # 1. 輸入帳號
        user_field = driver.find_element(By.ID, "iuser")
        user_field.send_keys(username)
        log_display.insert(tk.END, "已填入帳號...\n")

        # 2. 輸入密碼
        pw_field = driver.find_element(By.ID, "ipswd")
        pw_field.send_keys(password)
        log_display.insert(tk.END, "已填入密碼...\n")

        # 3. 點擊登入按鈕
        login_btn = driver.find_element(By.ID, "mybutton")
        login_btn.click()
        log_display.insert(tk.END, "已點擊登入，等待跳轉...\n")

        # 等待登入成功跳轉後的 Cookie
        time.sleep(5) 

        cookies = driver.get_cookies()
        log_display.insert(tk.END, "--- 登入成功！提取 Cookies ---\n")
        for cookie in cookies:
            log_display.insert(tk.END, f"{cookie['name']}: {cookie['value']}\n")
            
    except Exception as e:
        log_display.insert(tk.END, f"發生錯誤: {str(e)}\n")

# --- GUI 介面 ---
root = tk.Tk()
root.title("自動登入 Token 提取器")
root.geometry("600x600")

tk.Label(root, text="網址:").pack()
url_entry = tk.Entry(root, width=50)
url_entry.insert(0, "https://hp8.pokp02.net/")
url_entry.pack()

tk.Label(root, text="帳號:").pack()
user_entry = tk.Entry(root, width=30)
user_entry.pack()

tk.Label(root, text="密碼:").pack()
pw_entry = tk.Entry(root, width=30, show="*")
pw_entry.pack()

btn = tk.Button(root, text="開始自動登入並抓取", command=auto_login, bg="blue", fg="white")
btn.pack(pady=10)

log_display = scrolledtext.ScrolledText(root, width=70, height=20)
log_display.pack()

root.mainloop()