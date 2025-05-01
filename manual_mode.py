
# ------------------------------------------------------------------
import pygame, sys, math, os, json, datetime, random
from config import *
from assets import load_assets
from pytmx.util_pygame import load_pygame
 # GỌI POPUP THÔNG BÁO
import tkinter as tk
from tkinter import messagebox
RESULT_FILE = "./Data/manual_results.json"           # nơi lưu JSON

# ---------- Hàm tiện ích ghi/đọc JSON ----------
def _load_results():
    if not os.path.exists(RESULT_FILE):
        return []
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
def check_collision():
    for border in border_rects:
        if car.rect.colliderect(border):
            return True
    for col_sprite in sprite_col:
        if car.mask.overlap(pygame.mask.from_surface(col_sprite.image), (col_sprite.rect.x - car.rect.x, col_sprite.rect.y - car.rect.y)):
            return True
    for ped in pedestrian_sprites:
        if car.mask.overlap(ped.mask, (ped.rect.x - car.rect.x, ped.rect.y - car.rect.y)):
            return True
    return False

def _same(rec1, rec2):
    return (
        rec1["algorithm"] == rec2["algorithm"]
        and rec1["time"]      == rec2["time"]
        and rec1["distance"]  == rec2["distance"]
    )

def save_results_log(results_log):
    """Lưu toàn bộ bảng hiện tại vào JSON, chống trùng."""
    data = _load_results()
    added = 0
    for algo, t, dist in results_log:
        new_rec = {
            "algorithm": algo,
            "time"     : t,
            "distance" : dist
        }
        if any(_same(r, new_rec) for r in data):
            continue
        data.append(new_rec)
        added += 1
    if added:
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅  Đã lưu {added} bản ghi mới vào results.json")
    else:
        print("⏩  Không có bản ghi mới để lưu (đều trùng)")


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Car Game")
clock = pygame.time.Clock()

from assets import load_assets
CAR_IMAGE, PLAY_IMG, EMPTY_BTN_IMG, PEDESTRIAN_IMAGES, BUTTON_X, BUTTON_Y = load_assets(SCREEN_WIDTH, SCREEN_HEIGHT)

import Button
from car import Car
from pedestrian import spawn_random_pedestrian
from pathfinding import (
    a_star, bfs, dfs, count_turns,
    iddfs, greedy_bfs, simple_hill_climbing,
    genetic_algorithm, backtracking, q_learning_pathfinder
)
from map_loader import load_map_objects, create_grid_from_map
from game_state import *
menu_bg = pygame.image.load("bgr2.jpg").convert()
menu_bg = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

MENU_FONT_TITLE = pygame.font.SysFont("consolas", 60, bold=True)
MENU_FONT_BTN = pygame.font.SysFont("calibri", 36, bold=True)


playBtn = Button.Button(BUTTON_X, BUTTON_Y, PLAY_IMG, 0.4)
emptyBtn = Button.Button(BUTTON_X, BUTTON_Y + 100, EMPTY_BTN_IMG, 0.4)
saveBtn = Button.Button(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 80, EMPTY_BTN_IMG, 0.4)
autoBtn = Button.Button(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT - 80, EMPTY_BTN_IMG, 0.4)
save_json_rect = pygame.Rect((SCREEN_WIDTH - 100) // 2 - 110, SCREEN_HEIGHT - 50, 100, 40)




from pytmx.util_pygame import load_pygame
tmx_data = load_pygame("map.tmx")
sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group()
pedestrian_sprites = pygame.sprite.Group()
game_run = "game"
border_rects, pedestrian_paths, Start_X, Start_Y = load_map_objects(tmx_data, sprite_group, sprite_col)
grid = create_grid_from_map(tmx_data, CELL_SIZE)
dynamic_grid = [row[:] for row in grid]
is_auto_mode = False
car = Car(Start_X, Start_Y, 43, 74, CAR_IMAGE, border_rects)
prev_car_position = (int(car.y) // CELL_SIZE, int(car.x) // CELL_SIZE)
CURRENT_ALGO = "a_star"

PANEL_RECT = pygame.Rect(SCREEN_WIDTH - 240, SCREEN_HEIGHT - 350, 170, 300) 
BTN_RECTS = {
    "bfs": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 10, 130, 25),
    "dfs": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 40, 130, 25),
    "iddfs": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 70, 130, 25),
    "greedy": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 100, 130, 25),
    "a_star": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 130, 130, 25),
    "hc": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 160, 130, 25),
    "ga": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 190, 130, 25),
    "bt": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 220, 130, 25),
    "ql": pygame.Rect(PANEL_RECT.x + 15, PANEL_RECT.y + 250, 130, 25),
}

results_log = []
# -- Dialog popup
dialog_mode = None  # None, 'success', 'collision'
show_dialog = False
dialog_rect = pygame.Rect((SCREEN_WIDTH - 400)//2, (SCREEN_HEIGHT - 200)//2, 400, 200)
ok_button_rect = pygame.Rect(dialog_rect.centerx - 60, dialog_rect.bottom - 60, 120, 40)

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_algo_panel():
    pygame.draw.rect(screen, ALGO_PANEL_BG, PANEL_RECT)
    pygame.draw.rect(screen, ALGO_PANEL_BORDER, PANEL_RECT, 2)
    for key, rect in BTN_RECTS.items():
        bg = ALGO_BTN_ACTIVE if key == CURRENT_ALGO else ALGO_BTN_INACTIVE
        pygame.draw.rect(screen, bg, rect, border_radius=4)
        label = "A*" if key == "a_star" else key.upper()
        txt = FONT_ALGO.render(label, True, (0, 0, 0))
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
def compute_path(grid, start, goal):
    if CURRENT_ALGO == "bfs": return bfs(grid, start, goal)
    elif CURRENT_ALGO == "dfs": return dfs(grid, start, goal)
    elif CURRENT_ALGO == "iddfs": return iddfs(grid, start, goal)
    elif CURRENT_ALGO == "greedy": return greedy_bfs(grid, start, goal)
    elif CURRENT_ALGO == "hc": return simple_hill_climbing(grid, start, goal)
    elif CURRENT_ALGO == "ga": return genetic_algorithm(grid, start, goal)
    elif CURRENT_ALGO == "bt": return backtracking(grid, start, goal)
    return a_star(grid, start, goal)



while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if show_dialog:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ok_button_rect.collidepoint(event.pos):
                    # Reset lại game
                    car.x, car.y = Start_X, Start_Y
                    car.rect.topleft = (int(car.x), int(car.y))
                    car.speed, car.angle = 0, 0
                    car.auto_mode = False
                    pedestrian_sprites.empty()
                    user_goal_cell = None
                    user_goal_rect = None
                    path = []
                    path_time = 0
                    path_length = 0
                    block_frames = 0
                    clear_frames = 0
                    prev_car_position = (int(car.y) // CELL_SIZE, int(car.x) // CELL_SIZE)
                    show_dialog = False
                    dialog_mode = None
                    game_run = "game"
            continue  # Nếu đang show dialog thì không xử lý các nút khác
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_run == "game":
            if save_rect.collidepoint(event.pos):
                if user_goal_cell:
                    results_log.append((CURRENT_ALGO.upper(), round(path_time, 1), path_length))
            if save_json_rect.collidepoint(event.pos):
                save_results_log(results_log)
            if autoBtn.rect.collidepoint(event.pos):
                if path:
                    car.start_auto_mode(path)
            for key, rect in BTN_RECTS.items():
                if rect.collidepoint(event.pos):
                    CURRENT_ALGO = key
                    if user_goal_cell:
                        car_rc = (int(car.y)//CELL_SIZE, int(car.x)//CELL_SIZE)
                        path = compute_path(dynamic_grid, car_rc, user_goal_cell)
                        if path:
                            path_length = len(path)
                            path_time = path_length * 1.0 + count_turns(path) * 0.5
                    break
            else:
                mx, my = event.pos
                col, row = mx // CELL_SIZE, my // CELL_SIZE
                if 0 <= row < len(grid) and 0 <= col < len(grid[0]) and grid[row][col] == 0:
                    user_goal_cell = (row, col)
                    user_goal_rect = pygame.Rect(col*CELL_SIZE, row*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    car_rc = (int(car.y)//CELL_SIZE, int(car.x)//CELL_SIZE)
                    path = compute_path(dynamic_grid, car_rc, user_goal_cell)
                    if path:
                        path_length = len(path)
                        path_time = path_length * 1.0 + count_turns(path) * 0.5

   

    if game_run == "game":
        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (255,165,0), save_json_rect, border_radius=10)  # cam
        txt_json = FONT_INFO.render("JSON", True, (0,0,0))
        screen.blit(txt_json, (save_json_rect.centerx - txt_json.get_width()//2,
                               save_json_rect.centery - txt_json.get_height()//2))
        # === Nút AUTO bên cạnh nút SAVE ===
        auto_rect = pygame.Rect((SCREEN_WIDTH - 100) // 2 + 110, SCREEN_HEIGHT - 50, 100, 40)
        pygame.draw.rect(screen, (0, 170, 255), auto_rect, border_radius=10)  # light blue
        auto_txt = FONT_INFO.render("AUTO", True, (255, 255, 255))
        screen.blit(auto_txt, (
            auto_rect.x + (auto_rect.width - auto_txt.get_width()) // 2,
            auto_rect.y + (auto_rect.height - auto_txt.get_height()) // 2
        ))






        keys = pygame.key.get_pressed()
        if car.auto_mode and (keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
            car.auto_mode = False
        if not car.auto_mode:
            if keys[pygame.K_UP]: car.speed += ACCEL
            if keys[pygame.K_DOWN]: car.speed -= DECEL
            car.speed *= FRICTION
            if keys[pygame.K_LEFT]: car.angle += TURN * (car.speed / 5)
            if keys[pygame.K_RIGHT]: car.angle -= TURN * (car.speed / 5)

            car.x -= car.speed * math.sin(math.radians(car.angle))
            car.y -= car.speed * math.cos(math.radians(-car.angle))
            car.rect.topleft = (int(car.x), int(car.y))
        else:
            car.update_auto_move()

        
        if check_collision() and not show_dialog:
            car.speed = 0
            show_dialog = True
            dialog_mode = "collision"

        for col_sprite in sprite_col:
            if car.mask.overlap(pygame.mask.from_surface(col_sprite.image), (col_sprite.rect.x - car.rect.x, col_sprite.rect.y - car.rect.y)):
                car.x, car.y = Start_X, Start_Y
                car.speed, car.angle = 0, 0
                game_run = "col"

        for ped in pedestrian_sprites:
            if car.mask.overlap(ped.mask, (ped.rect.x - car.rect.x, ped.rect.y - car.rect.y)):
                car.x, car.y = Start_X, Start_Y
                car.speed, car.angle = 0, 0
                game_run = "col"

        
        if user_goal_rect and car.rect.colliderect(user_goal_rect) and not show_dialog:
            car.speed = 0
            show_dialog = True
            dialog_mode = "success"
 


        
        sprite_group.draw(screen)
        sprite_col.draw(screen)
        car.draw(screen)
        draw_algo_panel()
        


        current_time = pygame.time.get_ticks()
        if (current_time - spawn_timer > next_spawn_interval 
            and pedestrian_paths 
            and len(pedestrian_sprites) < 3):  # chỉ khi < 2 người

            spawn_random_pedestrian(pedestrian_paths, pedestrian_sprites, PEDESTRIAN_IMAGES)
            spawn_timer = current_time
            next_spawn_interval = random.randint(MIN_SPAWN_TIME, MAX_SPAWN_TIME)


        pedestrian_sprites.update()
        dynamic_grid = [row[:] for row in grid]

        for ped in pedestrian_sprites:
            pr = int(ped.rect.centery // CELL_SIZE)
            pc = int(ped.rect.centerx // CELL_SIZE)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r, c = pr + dr, pc + dc
                    if 0 <= r < len(dynamic_grid) and 0 <= c < len(dynamic_grid[0]):
                        dynamic_grid[r][c] = 1

        car_row, car_col = int(car.y) // CELL_SIZE, int(car.x) // CELL_SIZE
        blocked_now = path and any(dynamic_grid[r][c] for r, c in path)

        if blocked_now:
            block_frames += 1
            clear_frames = 0
        else:
            clear_frames += 1
            block_frames = 0

        if block_frames == BLOCK_DEBOUNCE_FRAMES and user_goal_cell:
            path = compute_path(dynamic_grid, (car_row, car_col), user_goal_cell)
            if path:
                path_length = len(path)
                path_time = path_length * 1.0 + count_turns(path) * 0.5
        elif clear_frames == CLEAR_DEBOUNCE_FRAMES and user_goal_cell:
            path = compute_path(grid, (car_row, car_col), user_goal_cell)
            if path:
                path_length = len(path)
                path_time = path_length * 1.0 + count_turns(path) * 0.5
        elif (car_row, car_col) != prev_car_position and not blocked_now and user_goal_cell:
            prev_car_position = (car_row, car_col)
            path = compute_path(grid, (car_row, car_col), user_goal_cell)
            if path:
                path_length = len(path)
                path_time = path_length * 1.0 + count_turns(path) * 0.5

        pedestrian_sprites.draw(screen)
        if user_goal_rect:
            pygame.draw.rect(screen, (0, 255, 0), user_goal_rect, 0)  # xanh lá full
            pygame.draw.rect(screen, (255, 255, 255), user_goal_rect, 3)  # viền trắng
        if path:
            for i in range(1, len(path)):
                prev_row, prev_col = path[i - 1]
                curr_row, curr_col = path[i]
                x = curr_col * CELL_SIZE + CELL_SIZE // 2
                y = curr_row * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(screen, (255, 0, 0), (x, y), 8)

        # Bảng luôn hiển thị ở góc trái trên cùng
        table_x, table_y = 20, 20
        row_h = 30
        headers = ["METHOD", "TIME", "DISTANCE"]
        for i, header in enumerate(headers):
            txt = FONT_INFO.render(header, True, (0, 255, 255))
            screen.blit(txt, (table_x + i * 200, table_y))
        for idx, (algo, time, steps) in enumerate(results_log[-10:]):
            screen.blit(FONT_INFO.render(algo, True, (255, 255, 255)), (table_x, table_y + (idx + 1) * row_h))
            screen.blit(FONT_INFO.render(str(time), True, (255, 255, 255)), (table_x + 200, table_y + (idx + 1) * row_h))
            screen.blit(FONT_INFO.render(str(steps), True, (255, 255, 255)), (table_x + 400, table_y + (idx + 1) * row_h))

        txt1 = FONT_INFO.render(f"{CURRENT_ALGO.upper()} Path: {path_length} steps", True, (255, 255, 0))
        txt2 = FONT_INFO.render(f"Time: {path_time:.1f}s", True, (255, 255, 0))
        screen.blit(txt1, (20, SCREEN_HEIGHT - 35))
        screen.blit(txt2, (SCREEN_WIDTH - txt2.get_width() - 20, SCREEN_HEIGHT - 35))
        # === Nút SAVE giữa màn hình với nền xanh và chữ trắng ===
        save_rect = pygame.Rect((SCREEN_WIDTH - 100) // 2, SCREEN_HEIGHT - 50, 100, 40)
        pygame.draw.rect(screen, (144, 238, 144), save_rect, border_radius=10)  # light green
        save_txt = FONT_INFO.render("SAVE", True, (255, 255, 255))
        screen.blit(save_txt, (
            save_rect.x + (save_rect.width - save_txt.get_width()) // 2,
            save_rect.y + (save_rect.height - save_txt.get_height()) // 2
        ))
        if show_dialog:
            pygame.draw.rect(screen, (255, 255, 255), dialog_rect, border_radius=12)
            pygame.draw.rect(screen, (0, 0, 0), dialog_rect, 3, border_radius=12)

            msg = "🚗 Successfully!" if dialog_mode == "success" else "💥 Va chạm!"
            text = FONT_MAIN.render(msg, True, (0, 0, 0))
            screen.blit(text, (dialog_rect.centerx - text.get_width() // 2, dialog_rect.y + 50))

            pygame.draw.rect(screen, (0, 170, 0), ok_button_rect, border_radius=8)
            ok_text = FONT_INFO.render("OK", True, (255, 255, 255))
            screen.blit(ok_text, (ok_button_rect.centerx - ok_text.get_width() // 2,
                                ok_button_rect.centery - ok_text.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)

    
