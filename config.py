import pygame

# === Cấu hình màn hình ===
CELL_SIZE = 64
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080

# === Cấu hình màu sắc ===
TEXT_COL = (255, 255, 255)
ALGO_PANEL_BG = (40, 40, 40)
ALGO_PANEL_BORDER = (200, 200, 200)
ALGO_BTN_ACTIVE = (120, 200, 120)
ALGO_BTN_INACTIVE = (120, 120, 120)

# === Font ===
pygame.font.init()
FONT_MAIN = pygame.font.SysFont("calibri", 72)
FONT_ALGO = pygame.font.SysFont("consolas", 20, bold=True)
FONT_INFO = pygame.font.SysFont("consolas", 24)

# === Game speed & logic ===
ACCEL = 0.1
DECEL = 0.05
FRICTION = 0.98
TURN = 2

# === Spawn pedestrian timing (ms) ===
MIN_SPAWN_TIME = 5000
MAX_SPAWN_TIME = 14000

# === Debounce frame settings ===
BLOCK_DEBOUNCE_FRAMES = 6
CLEAR_DEBOUNCE_FRAMES = 12