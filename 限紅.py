from logging import log
import os
import re
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

#        input("⏸ 已暫停（畫面保留中），處理完請按 Enter 繼續或關閉…") debug時需要


CONFIG_PATH = Path("config_cache.json")

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")



def run_to_userlist_and_fill_WM(username: str, password: str, target_list: list, headless: bool, log_fn, process_group_a: bool, process_group_b: bool, process_group_c: bool = True):
    def log(msg: str):
        log_fn(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # 1) 打開登入頁
        log("🔐 打開登入頁…")
        page.goto("https://hp8.pokp02.net/index.php?ctrl=login_c.php", wait_until="domcontentloaded")
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

        logged_in = False
        try:
            page.wait_for_url("**ctrl=ctrl_home**", timeout=5000)
            logged_in = True
            log("✅ 已登入成功（URL 判斷）")
        except:
            log("⚠️ URL 尚未進入 ctrl_home，準備第二次登入")
        if not logged_in:
            try:
                log("🔁 送出登入（第二次）")
                login_btn.scroll_into_view_if_needed(timeout=3000)
                login_btn.click(force=True)

                page.wait_for_url("**ctrl=ctrl_home**", timeout=8000)
                log("✅ 已登入成功（第二次 URL）")
            except Exception:
                log("❌ 第二次登入仍未進入 ctrl_home，繼續流程")




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
        for target_account in target_list:
            try:
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
                # 1. 定義分組
                groups = {
                    "群組 10K (4, 8, 13, 17, 58)": ["4", "8", "13", "17", "58"],
                    "群組 20K (21, 23, 25, 27, 172)": ["21", "23", "25", "27", "172"],
                    "群組 5K (3, 7, 12, 16, 57)": ["3", "7", "12", "16", "57"]
                }

                # 確保頁面加載
                frame.locator("text=Code").first.wait_for(state="visible", timeout=15000)

                groups_to_process = {}
                if process_group_a:
                    groups_to_process["群組 10K (4, 8, 13, 17, 58)"] = groups["群組 10K (4, 8, 13, 17, 58)"]
                if process_group_b:
                    groups_to_process["群組 20K (21, 23, 25, 27, 172)"] = groups["群組 20K (21, 23, 25, 27, 172)"]
                if process_group_c:
                    groups_to_process["群組 5K (3, 7, 12, 16, 57)"] = groups["群組 5K (3, 7, 12, 16, 57)"]

                for group_name, codes in groups_to_process.items():
                    log(f"\n--- 正在處理 {group_name} ---")
                    
                    for code in codes:
                        try:
                            # 定義號碼定位器
                            code_badge = frame.locator(f"xpath=//*[normalize-space(text())='{code}']").first
                            code_badge.wait_for(state="visible", timeout=5000)
                            # 找前面的 Checkbox 容器 (span)
                            box = code_badge.locator("xpath=preceding::span[1]").first                                                                                             
                            # 執行點擊 
                            click_target = box.locator("xpath=..").first
                            click_target.click(force=True)        
                        except Exception as e:
                            # 捕捉錯誤，不讓程式因為某個號碼沒找到就中斷
                            log(f"號碼 {code.ljust(3)}: ❌ 處理失敗 (找不到元素或超時)")

                        except Exception as e:
                            log(f"❌ 號碼 {code} 處理失敗: {str(e)}")
            except Exception as e:
                log(f"❌ 帳號 {target_account} 執行中斷: {e}")
                # 發生錯誤時，嘗試回到 User List 頁面嘗試下一個，不讓整個程式當掉
                page.goto("原本 User List 的 URL") 
                continue



        input("⏸ 已暫停（畫面保留中），處理完請按 Enter 繼續或關閉…")


        browser.close()
def run_site_E(username: str, password: str, target_list: list, headless: bool, log_fn, normal_max: str, deluxe_max: str):

    def log(msg: str):
        log_fn(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        log("🔐 SA：進入 https://bop.sa-bo.net ...")
        page.goto("https://bop.sa-bo.net", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        log("🌐 SiteE：準備切換語言到 English...")

        # 1) 點「简体中文」下拉（用 id 最穩）
        lang_btn = page.locator("#dropdownMenuLink")
        lang_btn.wait_for(state="visible", timeout=10000)
        lang_btn.click(force=True)

        # 2) 點 English（可能在 dropdown 裡，保守用文字匹配）
        en_item = page.locator('span.dropdown-item.cursor-pointer:has-text("English")')
        if en_item.count() == 0:
            # 兜底：有些站 dropdown-item 可能不是 span
            en_item = page.locator('.dropdown-item.cursor-pointer:has-text("English")')

        en_item.wait_for(state="visible", timeout=10000)
        en_item.click(force=True)

        page.wait_for_timeout(600)
        log("✅ SiteE：語言已切換為 English")

        user_input = page.get_by_placeholder("Username")
        pass_input = page.get_by_placeholder("Password")

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

        log("⏳ SiteE：等待登入成功（出現 Functions）...")
        page.get_by_text("Functions", exact=True).wait_for(timeout=180000)  # 給你 3 分鐘輸驗證碼
        log("✅ SiteE：偵測到 Functions（登入成功）")

        # 7) 點 Functions
        page.get_by_text("Functions", exact=True).click()
        page.wait_for_timeout(500)
        page.get_by_text("Account Management", exact=True).click()
        page.wait_for_timeout(500)

        log("🖱️ SiteE：點擊第一筆 Username")

            # 等 Account Management 表格出現
        page.locator("table").wait_for(timeout=15000)

        # 點第一個 Username 連結（藍色）
        username_link = page.locator("table a").first
        username_link.wait_for(state="visible", timeout=15000)
        username_link.click(force=True)
        page.wait_for_timeout(1000)
        username_link = page.locator("table a").first
        username_link.wait_for(state="visible", timeout=15000)
        username_link.click(force=True)

        log("✅ SiteE：已點擊第一筆 Username")
        for target_account in target_list:
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            log(f"🔎 將 Username 搜尋改為：{target_account}")

            # 1️⃣ 等 Username 搜尋框
            username_input = page.locator('input[name="searchUserName"], input[placeholder="Username"]').first
            username_input.wait_for(state="visible", timeout=15000)

            # 2️⃣ 清空（一定要這樣，不要只用 fill）
            username_input.click()
            username_input.press("Control+A")
            username_input.press("Backspace")

            # 3️⃣ 輸入 target account
            username_input.fill(f"{target_account}@a13154")

            # 4️⃣ 點 Search
            search_btn = page.locator('button:has-text("Search")').first
            search_btn.click(force=True)

            log("✅ 已送出 Username 搜尋")
            member_table = page.locator("table").nth(1)

            bet_icon = member_table.locator("i.icon-betlimit").first
            bet_icon.wait_for(state="visible", timeout=15000)
            bet_icon.scroll_into_view_if_needed()
            page.wait_for_timeout(200)

            # 方案 A：先點外層（很多時候真正可點的是 a/button/td）
            try:
                bet_clickable = bet_icon.locator("xpath=ancestor::a[1] | ancestor::button[1] | ancestor::td[1]").first
                bet_clickable.click(timeout=3000)
                log("✅ Bet Limit：已點外層容器")
            except Exception as e1:
                log(f"⚠️ 外層點擊失敗，改用中心點座標點擊：{e1}")

                # 方案 B：中心點座標點擊（必殺）
                box = bet_icon.bounding_box()
                if not box:
                    raise RuntimeError("抓不到 Bet Limit icon 的 bounding box（可能被遮住或不在視窗內）")

                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2

                page.mouse.click(x, y)
                page.wait_for_timeout(200)

                # 方案 C：再補一個 JS click（保險）
                try:
                    bet_icon.evaluate("(el) => el.click()")
                    log("✅ Bet Limit：中心點 + JS click 補刀完成")
                except Exception as e2:
                    log(f"⚠️ JS click 也失敗：{e2}")


            log("🎯 開始處理 Bet Limit 設定...")

            # 等待彈窗出現
            page.wait_for_timeout(1500)
            
            # 找到包含 Min/Max 的表格
            title = page.get_by_text("Game Bet Limit Options", exact=False).first
            title.wait_for(state="visible", timeout=10000)
            
            log("✅ Bet Limit 彈窗已開啟")
            # === 開始處理各個遊戲分頁 ===
            exclude_games = ["Carnival Treasure"]
            special_games = ["Deluxe Blackjack"]

            tab_names = [
                "Andar Bahar", "Baccarat", "Dragon Tiger", "Fish Prawn Crab",
                "Pok Deng", "Roulette", "Sic Bo", "Teen Patti 20-20",
                "Thai HiLo", "Ultra Roulette", "Xoc Dia",
                "Deluxe Blackjack",  # ✅ 你要處理它，就要把它放進來
            ]

            for game_name in tab_names:
                if game_name in exclude_games:
                    log(f"⏩ 跳過不處理：{game_name}")
                    continue

                log(f"🔄 正在處理遊戲：{game_name}")
                page.get_by_role("listitem").get_by_text(game_name, exact=True).click()
                page.wait_for_timeout(500)

                NORMAL_CHOICES = {"10000", "20000"}  # 想加 5000 就加
                DELUXE_CHOICES = {"10000", "20000"}

                if game_name == "Deluxe Blackjack":
                    uncheck_set = {("200", m) for m in DELUXE_CHOICES}   # 先清掉同 min 候選
                    check_set   = {("200", deluxe_max)}                  # 再勾你選的
                    log(f"🎯 特殊處理：{game_name} → 勾 200-{deluxe_max}")
                else:
                    uncheck_set = {("100", m) for m in NORMAL_CHOICES}
                    check_set   = {("100", normal_max)}
                    log(f"🧩 一般處理：{game_name} → 勾 100-{normal_max}")

             
                try:
                    # 找到所有表格行
                    rows = page.locator("table:visible tr").all()
                    
                    for row in rows:
                        try:
                            # 獲取該行的 Min 和 Max 文字
                            cells = row.locator("td").all()
                            if len(cells) < 3:
                                continue
                                
                            # 檢查是否為 100 / 20,000 這一行
                            min_text = cells[1].inner_text().strip().replace(",", "")
                            max_text = cells[2].inner_text().strip().replace(",", "")

                            
                            if (min_text, max_text) in uncheck_set:

                                # 找到這一行的 checkbox
                                checkbox = row.locator("input[type='checkbox']").first
                                
                                # 檢查是否已勾選
                                is_checked = checkbox.is_checked()
                                
                                if is_checked:
                                    checkbox.click(force=True)
                                    log(f"🧹 已取消勾選：Min={min_text}, Max={max_text}")
                                else:
                                    log("ℹ️  Min=100, Max=20,000 原本就未勾選")
                                
                                
                        except:
                            continue
                            
                except Exception as e:
                    log(f"⚠️  取消勾選 100/20000 時發生錯誤: {e}")
                
                page.wait_for_timeout(500)
                
                # === 步驟 2: 勾選 Min=100, Max=10,000 ===
                try:
                    rows = page.locator("table:visible tr").all()
                    
                    for row in rows:
                        try:
                            cells = row.locator("td").all()
                            if len(cells) < 3:
                                continue
                                
                            # 檢查是否為 100 / 10,000 這一行
                            min_text = cells[1].inner_text().strip().replace(",", "")
                            max_text = cells[2].inner_text().strip().replace(",", "")
                            
                            if (min_text, max_text) in check_set:
                                checkbox = row.locator("input[type='checkbox']").first
                                
                                is_checked = checkbox.is_checked()
                                
                                if not is_checked:
                                    checkbox.click(force=True)
                                    log("✅ 已勾選：Min=100, Max=10,000")
                                else:
                                    log("ℹ️  Min=100, Max=10,000 原本就已勾選")
                                
                               
                        except:
                            continue
                            
                except Exception as e:
                    log(f"⚠️  勾選 100/10000 時發生錯誤: {e}")
                
                page.wait_for_timeout(500)

 


                log("🎉 Bet Limit 設定完成")

                        

            
        if not headless:
            input("⏸ SA 停在頁面，確認後按 Enter 繼續…")


        browser.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("五站台自動化工具（Notebook 分頁）")
        self.geometry("900x620")

        self.cfg = load_config()

        # ===== Notebook =====
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="x", padx=12, pady=10)

        self.tabs = {}
        self.site_names = ["WM", "SiteB", "SiteC", "SiteD", "SA"]

        for site in self.site_names:
            frame = ttk.Frame(self.nb, padding=10)
            self.nb.add(frame, text=site)
            self.tabs[site] = frame

            self._build_site_tab(frame, site)

        # ===== buttons =====
        btnfrm = ttk.Frame(self, padding=(12, 0, 12, 8))
        btnfrm.pack(fill="x")

        self.btn_run = ttk.Button(btnfrm, text="執行目前分頁", command=self.on_run_current_tab)
        self.btn_run.pack(side="left")

        self.var_headless = tk.BooleanVar(value=False)
        ttk.Checkbutton(btnfrm, text="背景執行（不顯示瀏覽器）", variable=self.var_headless)\
            .pack(side="left", padx=12)

        self.btn_clear = ttk.Button(btnfrm, text="清空 Log", command=lambda: self.txt.delete("1.0", "end"))
        self.btn_clear.pack(side="left", padx=8)

        # ===== log =====
        self.txt = ScrolledText(self, height=18)
        self.txt.pack(fill="both", expand=True, padx=12, pady=8)

        self.log("🟦 每個分頁是一個站台，每個站台有自己的帳密（會記憶在 config_cache.json）。")

    # -------------------------
    # 每個站台 tab 的 UI
    # -------------------------
    def _build_site_tab(self, parent, site: str):
        # 站台帳密（各自獨立）
        ttk.Label(parent, text=f"{site} 帳號").grid(row=0, column=0, sticky="w")
        var_user = tk.StringVar(value=self.cfg.get(site, {}).get("username", ""))
        ent_user = ttk.Entry(parent, textvariable=var_user, width=30)
        ent_user.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(parent, text=f"{site} 密碼").grid(row=0, column=2, sticky="w")
        var_pass = tk.StringVar(value=self.cfg.get(site, {}).get("password", ""))
        ent_pass = ttk.Entry(parent, textvariable=var_pass, show="*", width=30)
        ent_pass.grid(row=0, column=3, padx=8, pady=4, sticky="w")

        ttk.Separator(parent).grid(row=1, column=0, columnspan=4, sticky="ew", pady=10)

        # targets（每站都先放，之後你可改成該站特有欄位）
        ttk.Label(parent, text="targets (每行一個)").grid(row=2, column=0, sticky="nw")
        txt_targets = ScrolledText(parent, width=34, height=6)
        txt_targets.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        # WM 有群組
        wm_vars = None
        if site == "WM":
            ttk.Label(parent, text="WM 群組").grid(row=3, column=0, sticky="w", pady=(6, 0))
            var_c = tk.BooleanVar(value=True)
            var_a = tk.BooleanVar(value=True)
            var_b = tk.BooleanVar(value=True)

            rowbox = ttk.Frame(parent)
            rowbox.grid(row=3, column=1, sticky="w", pady=(6, 0))
            ttk.Checkbutton(rowbox, text="群組 5K", variable=var_c).pack(side="left")
            ttk.Checkbutton(rowbox, text="群組 10K", variable=var_a).pack(side="left", padx=10)
            ttk.Checkbutton(rowbox, text="群組 20K", variable=var_b).pack(side="left")

            wm_vars = (var_a, var_b, var_c)

        # 把變數存起來，on_run 讀得到
        self.tabs[site].vars = {
            "user": var_user,
            "pass": var_pass,
            "targets": txt_targets,
            "wm_groups": wm_vars
        }
        if site == "SA":
            ttk.Label(parent, text="Bet Limit 選項").grid(row=3, column=0, sticky="nw", pady=(6, 0))

            opt = ttk.Frame(parent)
            opt.grid(row=3, column=1, columnspan=3, sticky="w", pady=(6, 0))

            # 一般遊戲（Min=100）
            ttk.Label(opt, text="一般遊戲 Min=100 要勾 Max：").grid(row=0, column=0, sticky="w")
            var_normal_max = tk.StringVar(value="10000")  # ✅ 預設不變
            cb_normal = ttk.Combobox(
                opt, textvariable=var_normal_max,
                values=["10000", "20000"],  # 你要加 5000 就加進來
                width=10, state="readonly"
            )
            cb_normal.grid(row=0, column=1, padx=8, sticky="w")
            ttk.Label(opt, text="(10,000 / 20,000)").grid(row=0, column=2, sticky="w")

            # Deluxe Blackjack（Min=200）
            ttk.Label(opt, text="Deluxe Blackjack Min=200 要勾 Max：").grid(row=1, column=0, sticky="w", pady=(6, 0))
            var_deluxe_max = tk.StringVar(value="10000")  # ✅ 預設不變
            cb_deluxe = ttk.Combobox(
                opt, textvariable=var_deluxe_max,
                values=["10000", "20000"],
                width=10, state="readonly"
            )
            cb_deluxe.grid(row=1, column=1, padx=8, sticky="w", pady=(6, 0))
            ttk.Label(opt, text="(10,000 / 20,000)").grid(row=1, column=2, sticky="w", pady=(6, 0))

            # 存起來給 on_run 讀
            self.tabs[site].vars["normal_max"] = var_normal_max
            self.tabs[site].vars["deluxe_max"] = var_deluxe_max


    # -------------------------
    # log
    # -------------------------
    def log(self, msg: str):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.update_idletasks()

    # -------------------------
    # 執行：依目前分頁跑對應站台
    # -------------------------
    def on_run_current_tab(self):
        headless = self.var_headless.get()

        current_tab = self.nb.select()
        site = self.nb.tab(current_tab, "text")  # WM / SiteB...

        v = self.tabs[site].vars
        username = v["user"].get().strip()
        password = v["pass"].get().strip()
        raw = v["targets"].get("1.0", "end").strip()
        targets = [x.strip() for x in raw.splitlines() if x.strip()]

        if not username or not password:
            messagebox.showerror("缺少資料", f"{site}：請輸入帳號/密碼")
            return
        

        # 先存帳密（每站各自記憶）
        self.cfg[site] = {"username": username, "password": password}
        save_config(self.cfg)

        self.btn_run.config(state="disabled")
        self.log(f"▶ 開始：站台={site} targets={len(targets)} headless={headless}")

        def worker():
            try:
                if site == "WM":
                    var_a, var_b, var_c = v["wm_groups"]
                    process_a = var_a.get()
                    process_b = var_b.get()
                    process_c = var_c.get()
                    if not (process_a or process_b or process_c):
                        raise RuntimeError("WM：請至少勾選一個群組")

                    run_to_userlist_and_fill_WM(
                        username, password, targets, headless, self.log,
                        process_a, process_b, process_c
                    )
                else:
                    if site == "SA":
                        normal_max = v["normal_max"].get()  # e.g. "10000" / "20000"
                        deluxe_max = v["deluxe_max"].get()  # e.g. "10000" / "20000"
                        run_site_E(username, password, targets, headless, self.log, normal_max, deluxe_max)
                  

                    else:
                        self.log(f"🟨 {site} 尚未實作：先只做 SA")


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