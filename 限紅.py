import os
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

LOGIN_URL = "https://hp8.pokp02.net/index.php?ctrl=login_c.php"


def run_to_userlist_and_fill(username: str, password: str, target_account: str, headless: bool, log_fn):
    def log(msg: str):
        log_fn(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # 1) 打開登入頁
        log("🔐 打開登入頁…")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(600)

        # 2) 找到帳密輸入框
        user_input = page.locator(
            'input[placeholder*="账号"], input[placeholder*="帳號"], input[name*="user"], input[name*="account"], input[name*="login"]'
        ).first
        pass_input = page.locator(
            'input[type="password"], input[placeholder*="密码"], input[placeholder*="密碼"]'
        ).first

        # 兜底
        if user_input.count() == 0:
            user_input = page.locator('input[type="text"]').first
        if pass_input.count() == 0:
            pass_input = page.locator('input[type="password"]').first

        if user_input.count() == 0 or pass_input.count() == 0:
            browser.close()
            raise RuntimeError("找不到登入輸入框（帳號/密碼）")

        # 3) 輸入帳密
        log("✍️ 輸入帳密…")
        user_input.click()
        user_input.fill(username)
        pass_input.click()
        pass_input.fill(password)

        # 4) 點登入
        login_btn = page.get_by_role("button", name="登入")
        if login_btn.count() == 0:
            login_btn = page.locator('button:has-text("登入"), input[type="submit"], button[type="submit"]').first
        if login_btn.count() == 0:
            browser.close()
            raise RuntimeError("找不到登入按鈕")

        log("➡️ 送出登入…")
        login_btn.click()

        # 5) 等登入成功（不要用 expect_navigation）
        try:
            page.wait_for_url("**ctrl=ctrl_home**", timeout=15000)
        except PWTimeout:
            page.locator("text=用户管理").wait_for(timeout=15000)

        log(f"✅ 已登入：{page.url}")
        page.wait_for_timeout(400)

        # 6) 左側選單：用户管理 → 用户列表
        log("📂 前往：用户管理 → 用户列表")
        page.get_by_text("用户管理", exact=True).click()
        page.wait_for_timeout(200)
        page.get_by_text("用户列表", exact=True).click()

        # 7) 等「請搜尋帳號」輸入框出現並 fill
        log(f"🔎 填入搜尋帳號：{target_account}")
        search_input = page.locator(
            'input[placeholder="请搜寻帐号"], input[placeholder*="搜尋"], input[placeholder*="搜索"]'
        ).first
        search_input.wait_for(timeout=15000)
        search_input.click()
        search_input.fill(target_account)

        log("🟢 已填入完成。現在停住讓你確認畫面（不按搜尋）。")
        # 8) 停住：不關瀏覽器，讓你目視確認
        page.pause()
        # 如果你按「Resume」繼續，這裡才會跑到 close
        browser.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WM 用戶列表 - 自動填入搜尋帳號")
        self.geometry("720x440")

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="x")

        ttk.Label(frm, text="管理員帳號").grid(row=0, column=0, sticky="w")
        self.var_user = tk.StringVar(value=os.getenv("WM_USER", "acentd"))
        ttk.Entry(frm, textvariable=self.var_user, width=26).grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="管理員密碼").grid(row=0, column=2, sticky="w")
        self.var_pass = tk.StringVar(value=os.getenv("WM_PASS", "acentd"))
        ttk.Entry(frm, textvariable=self.var_pass, show="*", width=26).grid(row=0, column=3, padx=8, pady=4, sticky="w")

        ttk.Separator(frm).grid(row=1, column=0, columnspan=4, sticky="ew", pady=10)

        ttk.Label(frm, text="要填入的搜尋帳號").grid(row=2, column=0, sticky="w")
        self.var_target = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_target, width=26).grid(row=2, column=1, padx=8, pady=4, sticky="w")

        self.var_headless = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="背景執行（不顯示瀏覽器）", variable=self.var_headless).grid(
            row=2, column=3, sticky="w"
        )

        btnfrm = ttk.Frame(self, padding=(12, 0, 12, 8))
        btnfrm.pack(fill="x")

        self.btn_run = ttk.Button(btnfrm, text="執行並填入", command=self.on_run)
        self.btn_run.pack(side="left")

        self.btn_clear = ttk.Button(btnfrm, text="清空 Log", command=lambda: self.txt.delete("1.0", "end"))
        self.btn_clear.pack(side="left", padx=8)

        self.txt = ScrolledText(self, height=16)
        self.txt.pack(fill="both", expand=True, padx=12, pady=8)

        self.log("🟦 輸入要搜尋的帳號後按「執行並填入」。程式會停在用戶列表頁，不會按搜尋。")

    def log(self, msg: str):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.update_idletasks()

    def on_run(self):
        username = self.var_user.get().strip()
        password = self.var_pass.get().strip()
        target = self.var_target.get().strip()
        headless = self.var_headless.get()

        if not username or not password:
            messagebox.showerror("缺少資料", "請輸入管理員帳號/密碼")
            return
        if not target:
            messagebox.showerror("缺少資料", "請輸入要填入的搜尋帳號")
            return
        if headless:
            messagebox.showinfo("提醒", "你勾了背景執行，但我們要停住給你看畫面，建議先不要勾。")

        self.btn_run.config(state="disabled")
        self.log(f"▶ 開始：target={target} headless={headless}")

        def worker():
            try:
                run_to_userlist_and_fill(username, password, target, headless, self.log)
                self.log("✅ 流程結束。")
            except Exception as e:
                self.log("💥 發生錯誤：")
                self.log(str(e))
                self.log(traceback.format_exc())
                messagebox.showerror("執行失敗", str(e))
            finally:
                self.btn_run.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
