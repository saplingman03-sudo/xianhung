import pygame
import random

# 初始化
pygame.init()
screen = pygame.display.set_mode((1200, 550))
pygame.display.set_caption("小雞過馬路：自動掛機版")
clock = pygame.time.Clock()

# --- 自動偵測中文字體 ---
def get_chinese_font(size):
    target_fonts = ['microsoftjhenghei', 'msgothic', 'simhei', 'arialunicode']
    available = pygame.font.get_fonts()
    for f in target_fonts:
        if f in available:
            return pygame.font.SysFont(f, size)
    return pygame.font.SysFont(None, size)

# --- 數字縮寫函數 ---
def format_number(num):
    """將大數字縮寫為 K、M、B 等格式"""
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"${num/1_000:.1f}K"
    else:
        return f"${num:.0f}"

font = get_chinese_font(22)
font_stat = get_chinese_font(18)
font_small = get_chinese_font(16)

# --- 顏色定義 ---
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
GREEN, RED, BLUE, YELLOW = (100, 255, 100), (255, 100, 100), (100, 100, 255), (255, 255, 0)
LIGHT_BLUE = (150, 200, 255)

# --- 數據變數 ---
balance = 1000
bet_options = [10, 50, 100, 200, 500, 1000]
bet_index = 2
bet_amount = bet_options[bet_index]
total_spent = 0
total_won = 0
current_step = 0
win_rate = 0.8
game_active = False
game_over = False
cashed_out = False

# --- 難度模式變數 ---
difficulty_mode = None  # None=未選, "easy"=簡單, "normal"=普通, "hard"=困難, "crazy"=瘋狂
difficulty_modes = {
    "easy": {"win_rate": 0.53, "multiplier": 1.8, "name": "簡單"},
    "normal": {"win_rate": 0.4, "multiplier": 2.4, "name": "普通"},
    "hard": {"win_rate": 0.24, "multiplier": 4.0, "name": "困難"},
    "crazy": {"win_rate": 0.12, "multiplier": 8.0, "name": "瘋狂"}
}

# --- 自動模式變數 ---
auto_mode = False
target_stop_step = 3
auto_rounds_left = 0

# --- 輸入模式變數 ---
input_mode = False
input_text = ""
add_credit_mode = False  # 開分模式

# --- 游戲速度變數 ---
game_speed = 1  # 遊戲播放速度倍數，預設×1
speed_show_menu = False  # 是否顯示速度菜單
speed_options = [1, 2, 5, 10, 100]
animation_speed = 10  # 小雞移動速度

# --- 提示文字變數 ---
hint_text = ""
hint_timer = 0
hint_duration = 180  # 提示顯示幀數（約3秒）

# --- 數字鍵盤按鈕 ---
numpad_buttons = []
numpad_x, numpad_y = 950, 100
for i in range(9):
    row = i // 3
    col = i % 3
    rect = pygame.Rect(numpad_x + col * 50, numpad_y + row * 45, 45, 40)
    numpad_buttons.append((rect, str(i + 1)))
# 底部三個按鈕：0, 清除, 確認
numpad_buttons.append((pygame.Rect(numpad_x, numpad_y + 135, 45, 40), "0"))
numpad_buttons.append((pygame.Rect(numpad_x + 50, numpad_y + 135, 45, 40), "C"))
numpad_buttons.append((pygame.Rect(numpad_x + 100, numpad_y + 135, 45, 40), "✓"))

# --- 開分快速按鈕 ---
credit_presets = [100, 500, 1000, 2000, 10000]
credit_buttons = []
credit_x, credit_y = 950, 100
for idx, value in enumerate(credit_presets):
    row = idx // 2
    col = idx % 2
    rect = pygame.Rect(credit_x + col * 95, credit_y + row * 45, 90, 40)
    credit_buttons.append((rect, value))
# 手動輸入按鈕
manual_input_rect = pygame.Rect(credit_x, credit_y + 3 * 45, 190, 40)

# --- 動畫變數 ---
chicken_x, target_x = 50, 50
chicken_y = 300
lane_width = 70

# --- 按鈕區域 ---
btn_bet_rect = pygame.Rect(50, 20, 130, 45)
btn_bet_up = pygame.Rect(190, 20, 30, 20)
btn_bet_down = pygame.Rect(190, 45, 30, 20)
btn_move_rect = pygame.Rect(240, 20, 130, 45)
btn_cash_rect = pygame.Rect(390, 20, 130, 45)
btn_auto_toggle = pygame.Rect(540, 20, 130, 45)
btn_step_up = pygame.Rect(680, 20, 30, 20)
btn_step_down = pygame.Rect(680, 45, 30, 20)
btn_round_up = pygame.Rect(830, 20, 30, 20)
btn_round_down = pygame.Rect(830, 45, 30, 20)
rounds_input_rect = pygame.Rect(870, 25, 80, 30)  # 可點擊輸入的區域
btn_add_credit = pygame.Rect(980, 20, 60, 30)
btn_clear_credit = pygame.Rect(1050, 20, 60, 30)
btn_speed_rect = pygame.Rect(980, 55, 130, 30)  # 遊戲速度按鈕

# --- 難度模式按鈕 ---
btn_easy = pygame.Rect(50, 450, 80, 40)
btn_normal = pygame.Rect(150, 450, 80, 40)
btn_hard = pygame.Rect(250, 450, 80, 40)
btn_crazy = pygame.Rect(350, 450, 80, 40)

def draw_button(rect, text, color, active=True):
    draw_color = color if active else GRAY
    pygame.draw.rect(screen, draw_color, rect, border_radius=10)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=10)
    txt = font.render(text, True, BLACK)
    screen.blit(txt, txt.get_rect(center=rect.center))

running = True
while running:
    screen.fill(WHITE)
    
    # 自動模式邏輯
    if auto_mode and chicken_x == target_x and not input_mode:
        if not game_active and auto_rounds_left > 0:
            if balance >= bet_amount:
                balance -= bet_amount
                total_spent += bet_amount
                auto_rounds_left -= 1
                current_step, chicken_x, target_x = 0, 50, 50
                game_active, game_over, cashed_out = True, False, False
            else:
                auto_mode = False
        elif game_active and not (game_over or cashed_out):
            if current_step < target_stop_step:
                if random.random() < win_rate:
                    current_step += 1
                    target_x += lane_width
                    hint_text = "你好厲害 繼續加油"
                    hint_timer = hint_duration
                else:
                    game_over, game_active = True, False
                    hint_text = "傻逼窮光蛋"
                    hint_timer = hint_duration
            else:
                # 根據難度模式計算奖金
                multiplier = difficulty_modes[difficulty_mode]["multiplier"]
                prize = int(bet_amount * (multiplier ** current_step))
                balance += prize
                total_won += prize
                cashed_out, game_active = True, False
    
    # 計算相機偏移（根據小雞位置動態調整視窗）
    camera_offset = max(0, chicken_x - 400)  # 當小雞超過400像素時開始右移視窗
    
    # 繪製背景
    pygame.draw.rect(screen, (240, 240, 240), (0, 150, 1200, 300))
    
    # 繪製無限制步數的背景線
    max_steps = int(camera_offset / lane_width) + 25
    for i in range(int(camera_offset / lane_width), max_steps):
        x = 50 + (i * lane_width) - camera_offset
        if -100 < x < 1300:  # 只繪製在屏幕可見範圍內的線
            pygame.draw.line(screen, (210, 210, 210), (x, 150), (x, 450), 2)
    
    # 繪製每一步的可得獎金（無限制步數）
    max_prize_steps = int(camera_offset / lane_width) + 20
    for step in range(max(1, int(camera_offset / lane_width)), max_prize_steps):
        x = 50 + (step * lane_width) - camera_offset
        if -50 < x < 1250:  # 只繪製在屏幕可見範圍內的文字
            if difficulty_mode:
                multiplier = difficulty_modes[difficulty_mode]["multiplier"]
                prize_at_step = bet_amount * (multiplier ** step)
            else:
                prize_at_step = bet_amount * (1.2 ** step)
            prize_text = format_number(prize_at_step)
            txt = font_small.render(prize_text, True, BLACK)
            screen.blit(txt, (x - txt.get_width() // 2, 120))

    # 事件偵測
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 鍵盤輸入（輸入模式）- 優先處理
        if input_mode and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                try:
                    if add_credit_mode:
                        amount = max(0, int(input_text)) if input_text else 0
                        balance += amount
                        add_credit_mode = False
                    else:
                        auto_rounds_left = max(0, int(input_text)) if input_text else 0
                except:
                    if not add_credit_mode:
                        auto_rounds_left = 0
                input_mode = False
            elif event.key == pygame.K_ESCAPE:
                input_mode = False
                add_credit_mode = False
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif event.unicode.isdigit() and len(input_text) < 8:
                input_text += event.unicode
            continue  # 輸入模式時跳過其他事件處理
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            # 數字鍵盤點擊處理（輸入模式時優先）
            if input_mode:
                for rect, value in numpad_buttons:
                    if rect.collidepoint(pos):
                        if value == "✓":  # 確認
                            try:
                                if add_credit_mode:
                                    amount = max(0, int(input_text)) if input_text else 0
                                    balance += amount
                                    add_credit_mode = False
                                else:
                                    auto_rounds_left = max(0, int(input_text)) if input_text else 0
                            except:
                                if not add_credit_mode:
                                    auto_rounds_left = 0
                            input_mode = False
                        elif value == "C":  # 清除
                            input_text = ""
                        elif len(input_text) < 8:  # 數字
                            input_text += value
                        break
                # 點擊鍵盤外部關閉
                numpad_area = pygame.Rect(numpad_x - 10, numpad_y - 40, 170, 230)
                rounds_area = pygame.Rect(rounds_input_rect.x - 10, rounds_input_rect.y - 10, 
                                         rounds_input_rect.width + 20, rounds_input_rect.height + 20)
                manual_area = pygame.Rect(manual_input_rect.x - 10, manual_input_rect.y - 10,
                                         manual_input_rect.width + 20, manual_input_rect.height + 20)
                if not numpad_area.collidepoint(pos) and not rounds_area.collidepoint(pos) and not manual_area.collidepoint(pos):
                    try:
                        if add_credit_mode:
                            amount = max(0, int(input_text)) if input_text else 0
                            balance += amount
                            add_credit_mode = False
                        else:
                            auto_rounds_left = max(0, int(input_text)) if input_text else 0
                    except:
                        if not add_credit_mode:
                            auto_rounds_left = 0
                    input_mode = False
                continue
            
            # 點擊開分快速按鈕或手動輸入（僅當開分菜單顯示時）
            if add_credit_mode and not input_mode:
                clicked = False
                for rect, value in credit_buttons:
                    if rect.collidepoint(pos):
                        balance += value
                        add_credit_mode = False
                        clicked = True
                        break
                
                # 點擊開分手動輸入按鈕
                if not clicked and manual_input_rect.collidepoint(pos):
                    add_credit_mode = True
                    input_mode = True
                    input_text = ""
                
                # 點擊菜單外部關閉
                if not clicked:
                    menu_area = pygame.Rect(credit_x - 5, credit_y - 35, 195, 250)
                    if not menu_area.collidepoint(pos):
                        add_credit_mode = False
                continue
            
            # 點擊回數區域進入輸入模式
            if rounds_input_rect.collidepoint(pos) and not add_credit_mode:
                add_credit_mode = False
                input_mode = True
                input_text = str(auto_rounds_left)
                continue
            
            # 遊戲速度菜單點擊處理
            if speed_show_menu and not input_mode:
                clicked = False
                speed_menu_y = 100
                for idx, multiplier in enumerate(speed_options):
                    speed_rect = pygame.Rect(950 + (idx % 2) * 95, speed_menu_y + (idx // 2) * 45, 90, 40)
                    if speed_rect.collidepoint(pos):
                        game_speed = multiplier
                        speed_show_menu = False
                        clicked = True
                        break
                
                # 點擊菜單外部關閉
                if not clicked:
                    menu_area = pygame.Rect(945, 65, 195, 150)
                    if not menu_area.collidepoint(pos):
                        speed_show_menu = False
                continue
            
            # --- 以下只在非輸入模式執行 ---
            if not input_mode:
                # --- 難度模式選擇（可隨時切換） ---
                if btn_easy.collidepoint(pos):
                    difficulty_mode = "easy"
                    win_rate = difficulty_modes["easy"]["win_rate"]
                elif btn_normal.collidepoint(pos):
                    difficulty_mode = "normal"
                    win_rate = difficulty_modes["normal"]["win_rate"]
                elif btn_hard.collidepoint(pos):
                    difficulty_mode = "hard"
                    win_rate = difficulty_modes["hard"]["win_rate"]
                elif btn_crazy.collidepoint(pos):
                    difficulty_mode = "crazy"
                    win_rate = difficulty_modes["crazy"]["win_rate"]
                
                # --- 調整下注金額 ---
                if btn_bet_up.collidepoint(pos) and not game_active:
                    bet_index = min(bet_index + 1, len(bet_options) - 1)
                    bet_amount = bet_options[bet_index]
                
                if btn_bet_down.collidepoint(pos) and not game_active:
                    bet_index = max(bet_index - 1, 0)
                    bet_amount = bet_options[bet_index]
                
                # --- 開分/洗分 ---
                if btn_add_credit.collidepoint(pos):
                    add_credit_mode = True
                if btn_clear_credit.collidepoint(pos):
                    balance = 0
                    total_spent = 0
                    total_won = 0
                
                # 自動開關
                if btn_auto_toggle.collidepoint(pos):
                    auto_mode = not auto_mode
                
                # 遊戲速度按鈕
                if btn_speed_rect.collidepoint(pos):
                    speed_show_menu = not speed_show_menu
                
                # 調整參數
                if btn_step_up.collidepoint(pos):
                    target_stop_step += 1
                if btn_step_down.collidepoint(pos):
                    target_stop_step = max(1, target_stop_step - 1)
                if btn_round_up.collidepoint(pos):
                    auto_rounds_left += 10
                if btn_round_down.collidepoint(pos):
                    auto_rounds_left = max(0, auto_rounds_left - 10)
                
                # 手動操作
                if chicken_x == target_x:
                    if btn_bet_rect.collidepoint(pos) and not game_active:
                        if balance >= bet_amount:
                            balance -= bet_amount
                            total_spent += bet_amount
                            current_step, chicken_x, target_x = 0, 50, 50
                            game_active, game_over, cashed_out = True, False, False
                    elif btn_move_rect.collidepoint(pos) and game_active and not (game_over or cashed_out):
                        if random.random() < win_rate:
                            current_step += 1
                            target_x += lane_width
                            hint_text = "你好厲害 繼續加油"
                            hint_timer = hint_duration
                        else:
                            game_over, game_active = True, False
                            hint_text = "傻逼窮光蛋"
                            hint_timer = hint_duration
                    elif btn_cash_rect.collidepoint(pos) and game_active and not (game_over or cashed_out):
                        if current_step > 0:
                            prize = int(bet_amount * (1.2 ** current_step))
                            balance += prize
                            total_won += prize
                            cashed_out, game_active = True, False

    # 平滑動畫（應用遊戲速度倍數）
    if chicken_x < target_x:
        chicken_x += animation_speed * game_speed
        if chicken_x > target_x:
            chicken_x = target_x

    # 繪製小雞（應用相機偏移）
    color = RED if game_over else (GREEN if cashed_out else YELLOW)
    display_chicken_x = chicken_x - camera_offset
    pygame.draw.rect(screen, color, (display_chicken_x, chicken_y, 40, 40), border_radius=5)
    pygame.draw.rect(screen, BLACK, (display_chicken_x, chicken_y, 40, 40), 2, border_radius=5)
    
    # 繪製提示文字
    if hint_timer > 0:
        hint_timer -= 1

    # 繪製按鈕
    draw_button(btn_bet_rect, f"下注 ${bet_amount}", YELLOW, not game_active)
    draw_button(btn_bet_up, "+", GRAY, not game_active)
    draw_button(btn_bet_down, "-", GRAY, not game_active)
    draw_button(btn_move_rect, "往前跨一步", GREEN, game_active and not (game_over or cashed_out))
    draw_button(btn_cash_rect, "領獎退出", BLUE, game_active and not (game_over or cashed_out))
    draw_button(btn_auto_toggle, "自動: " + ("ON" if auto_mode else "OFF"), RED if auto_mode else GRAY)
    
    # 開分按鈕 - 點擊時顯示鍵盤
    if add_credit_mode:
        draw_button(btn_add_credit, "開分", LIGHT_BLUE)
    else:
        draw_button(btn_add_credit, "開分", GREEN)
    
    draw_button(btn_clear_credit, "洗分", RED)
    
    # 遊戲速度按鈕
    if speed_show_menu:
        draw_button(btn_speed_rect, f"速度: ×{game_speed}", LIGHT_BLUE)
    else:
        draw_button(btn_speed_rect, f"速度: ×{game_speed}", GRAY)
    
    # 難度模式選擇（總是顯示，根據選擇狀態改變顏色）
    easy_color = LIGHT_BLUE if difficulty_mode == "easy" else GRAY
    normal_color = YELLOW if difficulty_mode == "normal" else GRAY
    hard_color = RED if difficulty_mode == "hard" else GRAY
    crazy_color = (255, 50, 150) if difficulty_mode == "crazy" else GRAY  # 深粉紅
    
    draw_button(btn_easy, "簡單", easy_color)
    draw_button(btn_normal, "普通", normal_color)
    draw_button(btn_hard, "困難", hard_color)
    draw_button(btn_crazy, "瘋狂", crazy_color)
    
    # 目標步數
    screen.blit(font.render(f"目標: {target_stop_step} 步", True, BLACK), (720, 30))
    draw_button(btn_step_up, "+", GRAY)
    draw_button(btn_step_down, "-", GRAY)
    
    # 回數顯示與輸入
    draw_button(btn_round_up, "+", GRAY)
    draw_button(btn_round_down, "-", GRAY)
    
    if input_mode:
        # 輸入模式：顯示對應的鍵盤
        if add_credit_mode:
            # 手動開分輸入模式：顯示數字鍵盤 + 輸入框
            # 輸入框
            pygame.draw.rect(screen, LIGHT_BLUE, rounds_input_rect, border_radius=5)
            pygame.draw.rect(screen, BLUE, rounds_input_rect, 3, border_radius=5)
            display_text = input_text if input_text else "0"
            txt = font.render(display_text, True, BLACK)
            screen.blit(txt, txt.get_rect(center=rounds_input_rect.center))
            # 提示文字
            hint = font_small.render("輸入金額 →", True, BLUE)
            screen.blit(hint, (870, 8))
            
            # 繪製數字鍵盤
            pygame.draw.rect(screen, (240, 240, 240), (numpad_x - 5, numpad_y - 35, 160, 220), border_radius=10)
            pygame.draw.rect(screen, GREEN, (numpad_x - 5, numpad_y - 35, 160, 220), 2, border_radius=10)
            
            # 標題
            title = font_small.render("輸入開分金額", True, BLACK)
            screen.blit(title, (numpad_x + 20, numpad_y - 28))
            
            for rect, value in numpad_buttons:
                if value == "✓":
                    color = GREEN
                elif value == "C":
                    color = RED
                else:
                    color = (220, 220, 220)
                
                pygame.draw.rect(screen, color, rect, border_radius=5)
                pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
                
                # 文字居中
                if value == "✓":
                    txt = font.render("OK", True, BLACK)
                else:
                    txt = font.render(value, True, BLACK)
                screen.blit(txt, txt.get_rect(center=rect.center))
        else:
            # 回數輸入模式：顯示數字鍵盤
            pygame.draw.rect(screen, LIGHT_BLUE, rounds_input_rect, border_radius=5)
            pygame.draw.rect(screen, BLUE, rounds_input_rect, 3, border_radius=5)
            display_text = input_text if input_text else "0"
            txt = font.render(display_text, True, BLACK)
            screen.blit(txt, txt.get_rect(center=rounds_input_rect.center))
            # 提示文字
            hint = font_small.render("用鍵盤輸入 →", True, BLUE)
            screen.blit(hint, (870, 8))
            
            # 繪製數字鍵盤
            pygame.draw.rect(screen, (240, 240, 240), (numpad_x - 5, numpad_y - 35, 160, 220), border_radius=10)
            pygame.draw.rect(screen, BLUE, (numpad_x - 5, numpad_y - 35, 160, 220), 2, border_radius=10)
            
            # 標題
            title = font_small.render("輸入回數", True, BLACK)
            screen.blit(title, (numpad_x + 35, numpad_y - 28))
            
            for rect, value in numpad_buttons:
                if value == "✓":
                    color = GREEN
                elif value == "C":
                    color = RED
                else:
                    color = (220, 220, 220)
                
                pygame.draw.rect(screen, color, rect, border_radius=5)
                pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
                
                # 文字居中
                if value == "✓":
                    txt = font.render("OK", True, BLACK)
                else:
                    txt = font.render(value, True, BLACK)
                screen.blit(txt, txt.get_rect(center=rect.center))
    elif add_credit_mode and not input_mode:
        # 顯示開分快速選單（點擊開分按鈕後）
        pygame.draw.rect(screen, (240, 240, 240), (credit_x - 5, credit_y - 35, 195, 250), border_radius=10)
        pygame.draw.rect(screen, GREEN, (credit_x - 5, credit_y - 35, 195, 250), 2, border_radius=10)
        
        # 標題
        title = font_small.render("開分金額", True, BLACK)
        screen.blit(title, (credit_x + 55, credit_y - 28))
        
        # 快速按鈕
        for rect, value in credit_buttons:
            pygame.draw.rect(screen, (220, 220, 220), rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, rect, 2, border_radius=5)
            txt = font.render(f"${value}", True, BLACK)
            screen.blit(txt, txt.get_rect(center=rect.center))
        
        # 手動輸入按鈕
        pygame.draw.rect(screen, LIGHT_BLUE, manual_input_rect, border_radius=5)
        pygame.draw.rect(screen, BLUE, manual_input_rect, 2, border_radius=5)
        manual_txt = font.render("手動輸入", True, BLACK)
        screen.blit(manual_txt, manual_txt.get_rect(center=manual_input_rect.center))
        
        # 關閉提示
        close_hint = font_small.render("按ESC關閉", True, GRAY)
        screen.blit(close_hint, (credit_x - 5, credit_y + 190))
    else:
        # 一般模式：可點擊區域（回數）
        pygame.draw.rect(screen, (220, 240, 255), rounds_input_rect, border_radius=5)
        pygame.draw.rect(screen, (100, 150, 200), rounds_input_rect, 2, border_radius=5)
        txt = font.render(f"{auto_rounds_left} 回", True, BLACK)
        screen.blit(txt, txt.get_rect(center=rounds_input_rect.center))
        # 提示文字
        hint = font_small.render("點擊輸入", True, GRAY)
        screen.blit(hint, (870, 8))
    
    # 遊戲速度菜單顯示
    if speed_show_menu and not input_mode and not add_credit_mode:
        pygame.draw.rect(screen, (240, 240, 240), (945, 65, 195, 150), border_radius=10)
        pygame.draw.rect(screen, GRAY, (945, 65, 195, 150), 2, border_radius=10)
        
        # 標題
        title = font_small.render("遊戲速度", True, BLACK)
        screen.blit(title, (1010, 70))
        
        # 速度按鈕
        speed_menu_y = 100
        for idx, multiplier in enumerate(speed_options):
            speed_rect = pygame.Rect(950 + (idx % 2) * 95, speed_menu_y + (idx // 2) * 45, 90, 40)
            color = LIGHT_BLUE if multiplier == game_speed else (220, 220, 220)
            pygame.draw.rect(screen, color, speed_rect, border_radius=5)
            pygame.draw.rect(screen, BLACK, speed_rect, 2, border_radius=5)
            txt = font.render(f"×{multiplier}", True, BLACK)
            screen.blit(txt, txt.get_rect(center=speed_rect.center))

    # 數據與統計
    current_prize = int(bet_amount * (1.2 ** current_step)) if current_step > 0 else 0
    stat_text = f"餘額: ${balance}  目前獎金: ${current_prize}"
    screen.blit(font.render(stat_text, True, BLACK), (50, 85))
    
    # 提示文字顯示在獎金旁邊
    if hint_timer > 0:
        hint_display = font.render(hint_text, True, RED)
        screen.blit(hint_display, (450, 85))
    
    pygame.draw.rect(screen, (30, 30, 30), (0, 500, 1200, 50))
    rtp = (total_won / total_spent * 100) if total_spent > 0 else 0
    stat_str = f"總花費: ${total_spent} | 總得獎: ${total_won} | 淨利: ${total_won - total_spent} | 實際RTP: {rtp:.1f}%"
    screen.blit(font_stat.render(stat_str, True, WHITE), (20, 515))

    pygame.display.flip()
    clock.tick(60 * game_speed)  # 根據遊戲速度調整幀率

pygame.quit()