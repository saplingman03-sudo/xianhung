import pygame
import random

# 初始化
pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("小雞過馬路：博弈模擬器")
font = pygame.font.SysFont("SimHei", 24)

# 顏色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 遊戲參數
win_rate = 0.8  # 每一格過關的機率 (80%)
current_step = 0
total_steps = 10
bet_amount = 100
multiplier = 1.2 # 每跨一格的倍率增幅
game_over = False
cashed_out = False

def draw_text(text, x, y, color=BLACK):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

running = True
while running:
    screen.fill(WHITE)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN and not game_over and not cashed_out:
            if event.key == pygame.K_SPACE:  # 按空白鍵往前走一格
                if random.random() < win_rate:
                    current_step += 1
                    if current_step == total_steps:
                        cashed_out = True
                else:
                    game_over = True
            
            if event.key == pygame.K_RETURN: # 按 Enter 領獎退出
                cashed_out = True

    # 計算當前獎金
    current_prize = bet_amount * (multiplier ** current_step)

    # 顯示畫面內容
    draw_text(f"當前步數: {current_step} / {total_steps}", 50, 50)
    draw_text(f"預估獎金: {current_prize:.2f}", 50, 100)
    draw_text("[空白鍵] 往前跨一步 (風險)", 50, 250)
    draw_text("[Enter] 領獎並退出", 50, 300)

    if game_over:
        draw_text("炸彈爆炸！小雞變成炸雞了，獎金歸零。", 50, 180, RED)
    elif cashed_out:
        draw_text(f"恭喜領獎！你獲得了 {current_prize:.2f}", 50, 180, GREEN)

    pygame.display.flip()

pygame.quit()