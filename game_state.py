from config import MIN_SPAWN_TIME, MAX_SPAWN_TIME
import pygame
import random

# === Trạng thái ban đầu ===
path = []
path_length = 0
path_time = 0

user_goal_cell = None
user_goal_rect = None

spawn_timer = 0
next_spawn_interval = random.randint(MIN_SPAWN_TIME, MAX_SPAWN_TIME)

game_run = "menu"

# Ghi nhớ vị trí xe trước đó (để phát hiện di chuyển)
prev_car_position = (0, 0)

# Đếm khung để kiểm tra trạng thái chặn / thoáng
block_frames = 0
clear_frames = 0