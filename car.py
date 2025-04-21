import pygame
import math

class Car:
    def __init__(self, x, y, height, width, image, border_rects):
        self.x = x - width / 2
        self.y = y - height / 2
        self.height = height
        self.width = width
        self.rect = pygame.Rect(self.x, self.y, height, width)
        self.surface = pygame.Surface((height, width), pygame.SRCALPHA)
        self.surface.blit(image, (0, 0))
        self.angle = 0
        self.speed = 0
        self.mask = pygame.mask.from_surface(pygame.transform.rotate(self.surface, self.angle))

        # Auto drive
        self.auto_mode = False
        self.auto_path = []
        self.auto_index = 0
        self.border_rects = border_rects

    def draw(self, screen):
        self.rect.topleft = (int(self.x), int(self.y))
        rotated = pygame.transform.rotate(self.surface, self.angle)
        surface_rect = self.surface.get_rect(topleft=self.rect.topleft)
        new_rect = rotated.get_rect(center=surface_rect.center)
        screen.blit(rotated, new_rect.topleft)

    def smooth_path(self, path):
        smoothed = []
        for i in range(len(path) - 1):
            x1, y1 = path[i][1] * 64 + 32, path[i][0] * 64 + 32
            x2, y2 = path[i + 1][1] * 64 + 32, path[i + 1][0] * 64 + 32
            steps = 5
            for t in range(steps):
                interp_x = x1 + (x2 - x1) * t / steps
                interp_y = y1 + (y2 - y1) * t / steps
                smoothed.append((interp_x, interp_y))
        smoothed.append((path[-1][1] * 64 + 32, path[-1][0] * 64 + 32))
        return smoothed

    def start_auto_mode(self, path):
        self.auto_path = self.smooth_path(path)  # use smooth path
        self.auto_index = 0
        self.auto_mode = True
        self.speed = 2.0

    def update_auto_move(self):
        if self.auto_mode and self.auto_index < len(self.auto_path):
            target_x, target_y = self.auto_path[self.auto_index]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)

            if distance < 5:
                self.auto_index += 1
            else:
                angle_rad = math.atan2(-dy, dx)
                self.angle = math.degrees(angle_rad) - 90

                # === PHÁT HIỆN VA CHẠM TRÊN TOÀN ĐƯỜNG RẼ ===
                steps = 5  # kiểm tra va chạm tại nhiều bước nhỏ trên đoạn di chuyển
                for i in range(1, steps + 1):
                    interp_x = self.x + (dx / steps) * i
                    interp_y = self.y + (dy / steps) * i
                    test_rect = pygame.Rect(interp_x, interp_y, self.width, self.height)

                    for obstacle in self.border_rects:
                        if test_rect.colliderect(obstacle):
                            self.auto_mode = False
                            self.speed = 0
                            print("\ud83d\udea8 Tự dừng do phát hiện đâm ở góc cua!")
                            return

                self.x += self.speed * math.cos(math.radians(self.angle + 90))
                self.y -= self.speed * math.sin(math.radians(self.angle + 90))

        elif self.auto_index >= len(self.auto_path):
            self.auto_mode = False
            self.speed = 0

            if self.auto_path:
                final_x, final_y = self.auto_path[-1]
                self.x = final_x - self.width / 2
                self.y = final_y - self.height / 2 + (64 - self.height) / 2

            if len(self.auto_path) >= 2:
                final = self.auto_path[-1]
                prev = self.auto_path[-2]
                dy = final[1] - prev[1]
                if abs(dy) > 0:
                    self.angle = 0 if dy < 0 else 180
                else:
                    self.angle = 0