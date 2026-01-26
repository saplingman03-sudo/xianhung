#封存 目前覺得沒有希望做自動化
import os
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

#        input("⏸ 已暫停（畫面保留中），處理完請按 Enter 繼續或關閉…") debug時需要

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

        # 切換語言為 English（登入前）
        page.locator("#language-type").click()
        page.wait_for_timeout(300)  # 給下拉一點動畫時間（可留）

        page.locator("#language-list-en").click()
        page.wait_for_timeout(500)  # 等語言套用

        user_input = page.get_by_placeholder("Account")
        pass_input = page.get_by_placeholder("password")

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


        login_btn = page.get_by_role("button", name="LOGIN")
        if login_btn.count() == 0:
            login_btn = page.locator('button:has-text("LOGIN"), input[type="submit"], button[type="submit"]').first


        log("➡️ 送出登入（第 1 次）")
        login_btn.scroll_into_view_if_needed()
        login_btn.click(force=True)

        page.wait_for_timeout(2000)

        log("➡️ 送出登入（第 2 次）")
        login_btn.scroll_into_view_if_needed()
        login_btn.click(force=True)



        # 5) 等登入成功（不要用 expect_navigation）
        try:
            page.wait_for_url("**ctrl=ctrl_home**", timeout=15000)
        except PWTimeout:
            page.locator("text=User Management").wait_for(timeout=15000)

        log(f"✅ 已登入：{page.url}")
        page.wait_for_timeout(400)

        log("📂 前往： User Management → User List")
        page.get_by_text("User Management", exact=True).click()
        page.wait_for_timeout(200)
        page.get_by_text("User List", exact=True).click()
        #input("⏸ 已暫停（畫面保留中），處理完請按 Enter 繼續或關閉…")

        # ✅ 等 User List 頁面穩定（你可以用你頁面上一定會出現的字）
        page.wait_for_timeout(8000)
        log("🧩 掃描所有 frames：找 search / placeholder …")

        keywords = ["id=\"search\"", "Please search", "name=\"account\"", "input#search"]
        hit_frames = []

        for i, f in enumerate(page.frames):
            try:
                html = f.content()
                hit = any(k in html for k in keywords)
                log(f"[frame {i}] url={f.url} hit={hit}")
                if hit:
                    hit_frames.append((i, f.url))
            except Exception as e:
                log(f"[frame {i}] url={f.url} read error: {e}")

        if not hit_frames:
            raise RuntimeError("所有 frame 都沒包含 search 相關字樣（可能是新分頁或更深層 iframe）")

        log(f"✅ 命中 frames: {hit_frames}")
        # 找第一個命中 frame
        target_frame = None
        for f in page.frames:
            try:
                html = f.content()
                if "id=\"search\"" in html or "Please search" in html or "name=\"account\"" in html:
                    target_frame = f
                    break
            except:
                pass

        if not target_frame:
            raise RuntimeError("命中 frame 列表存在，但取不到 target_frame（奇怪）")

        log(f"🎯 使用 frame: {target_frame.url}")

        search = target_frame.locator('input#search, input[name="account"]').first
        search.wait_for(state="attached", timeout=15000)
        search.click(force=True)
        search.fill(target_account)
        log(f"✅ 已填入：{target_account}")

        for i, f in enumerate(page.frames):
            print(i, f.url)
        target_frame = None
        for f in page.frames:
            if f.locator('a[data-target="#popwindow"]').count() > 0:
                target_frame = f
                break

        if not target_frame:
            raise RuntimeError("找不到 Search 按鈕所在的 frame")

        target_frame.locator('a[data-target="#popwindow"]').first.click(force=True)

        log("🚀 搜尋指令已送出！")

                # 1) 確認 popwindow 還在（保險）
        modal = target_frame.locator("#popwindow")
        modal.wait_for(state="visible", timeout=15000)

        log("🔎 搜尋結果彈窗已存在，準備點擊帳號…")

        # 2) 用 href 的 aid 參數找連結（最穩）
        aid = target_account
        result_link = modal.locator(f'a[href*="aid={aid}"]').first

        result_link.wait_for(state="visible", timeout=15000)
        result_link.click(force=True)

        log(f"✅ 已點擊 target account：{aid}")
        page.wait_for_timeout(8000)
        log("已等待八秒")
        log("✏️ 準備點擊 Edit 按鈕…")

        # Edit 按鈕通常在同一個 frame（User List 那個）
        edit_btn = target_frame.locator('button[onclick*="UserAdd.php"]').first

        edit_btn.wait_for(state="visible", timeout=15000)
        edit_btn.click(force=True)

        log("✅ 已點擊 Edit，進入編輯頁")
        page.wait_for_timeout(4000)
        log("已等待4秒")
        def find_frame_containing(page):
            """
            找出包含 Code / Handicap / Baccarat 的 iframe
            不吃可視範圍（就算畫面還沒滑到也能找到）
            """
            keywords = [
                "Handicap",
                "Code",
            ]

            for i, f in enumerate(page.frames):
                try:
                    hit = 0
                    for k in keywords:
                        if f.locator(f"text={k}").count() > 0:
                            hit += 1
                    if hit >= 1:  # 命中至少一個就很有可能
                        return f
                except:
                    pass

            return None
        frame = find_frame_containing(page)
        if not frame:
            raise RuntimeError("找不到包含 Code / Handicap 的 iframe")
        log("✅ 找到 Code/Handicap 的 iframe")
        # 1. 定義分組清單
# 1. 定義分組
        groups = {
            "群組 A (4, 8, 13, 17, 58)": ["4", "8", "13", "17", "58"],
            "群組 B (21, 23, 25, 27, 172)": ["21", "23", "25", "27", "172"]
        }

        # 確保頁面加載
        frame.locator("text=Code").first.wait_for(state="visible", timeout=15000)

        for group_name, codes in groups.items():
            log(f"\n--- 正在處理 {group_name} ---")
            
            for code in codes:
                try:
                    # 定義號碼定位器
                    code_badge = frame.locator(f"xpath=//*[normalize-space(text())='{code}']").first
                    code_badge.wait_for(state="visible", timeout=5000)

                    # 找前面的 Checkbox 容器 (span)
                    box = code_badge.locator("xpath=preceding::span[1]").first
                    
                    # --- 強化版狀態偵測 ---
                    # 獲取 class 屬性，若無則預設為空字串避免 .lower() 報錯
                    class_attr = box.get_attribute("class") or ""
                    
                    # 判斷方式：檢查 class 是否含 checked 或是否有 ✓ 符號
                    is_checked = "checked" in class_attr.lower() or "✓" in box.inner_text()
                    
                    status_text = "【V 已勾選】" if is_checked else "【X 未勾選】"
                    
                    # 執行點擊 (不論狀態，執行切換)
                    click_target = box.locator("xpath=..").first
                    click_target.click(force=True)
                    
                    log(f"號碼 {code.ljust(3)}: 原本 {status_text} -> 已執行切換")

                except Exception as e:
                    # 捕捉錯誤，不讓程式因為某個號碼沒找到就中斷
                    log(f"號碼 {code.ljust(3)}: ❌ 處理失敗 (找不到元素或超時)")

                except Exception as e:
                    log(f"❌ 號碼 {code} 處理失敗: {str(e)}")
        # # 1. 定義你想要點擊的所有號碼
        # target_codes = ["4", "8", "13", "17", "58", "21", "23", "25", "27", "172"]

        # # 2. 確保 Code 欄位已出現（只需做一次）
        # frame.locator("text=Code").first.wait_for(state="visible", timeout=15000)

        # # 3. 使用迴圈自動執行重複動作
        # for code in target_codes:
        #     try:
        #         # 定義目標數字的定位器
        #         code_badge = frame.locator(f"xpath=//*[normalize-space(text())='{code}']").first
        #         code_badge.wait_for(state="visible", timeout=15000)

        #         # 找數字前面的第一個 span (checkbox 容器)
        #         box = code_badge.locator("xpath=preceding::span[1]").first
        #         box.wait_for(state="attached", timeout=15000)

        #         # 點擊 box 的父層
        #         click_target = box.locator("xpath=..").first
        #         click_target.click(force=True)
                
        #         print(f"成功點擊號碼: {code}")
        #     except Exception as e:
        #         print(f"點擊號碼 {code} 時發生錯誤: {e}")


        # log(f"✅ 已點擊 Code={target_codes} 那列的 checkbox 欄位")











        input("⏸ 已暫停（畫面保留中），處理完請按 Enter 繼續或關閉…")



 

        # 8) 停住：不關瀏覽器，讓你目視確認
        #page.pause()
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
