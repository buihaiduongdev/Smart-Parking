import pygame
from config import FONT_MAIN, TEXT_COL, FONT_ALGO, ALGO_PANEL_BG, ALGO_PANEL_BORDER, ALGO_BTN_ACTIVE, ALGO_BTN_INACTIVE
from assets import BUTTON_X, BUTTON_Y, PLAY_IMG, EMPTY_BTN_IMG
import Button

# === Tạo nút chơi và nút rỗng ===
playBtn = Button.Button(BUTTON_X, BUTTON_Y, PLAY_IMG, 0.4)
emptyBtn = Button.Button(BUTTON_X, BUTTON_Y + 100, EMPTY_BTN_IMG, 0.4)

# === Bảng chọn thuật toán ===
PANEL_RECT = pygame.Rect(1920 - 240, 1080 - 270, 170, 150)
BTN_RECTS = {
    "a_star": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 10, 130, 25),
    "bfs"   : pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 45, 130, 25),
    "dfs"   : pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 80, 130, 25),
}

def draw_text(text, font, color, x, y, screen):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_algo_panel(screen, current_algo):
    pygame.draw.rect(screen, ALGO_PANEL_BG, PANEL_RECT)
    pygame.draw.rect(screen, ALGO_PANEL_BORDER, PANEL_RECT, 2)
    for key, rect in BTN_RECTS.items():
        bg = ALGO_BTN_ACTIVE if key == current_algo else ALGO_BTN_INACTIVE
        pygame.draw.rect(screen, bg, rect, border_radius=4)
        label = "A*" if key == "a_star" else key.upper()
        txt = FONT_ALGO.render(label, True, (0, 0, 0))
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))