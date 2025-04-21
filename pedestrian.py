# pedestrian.py
import pygame
import random
import math

class Pedestrian(pygame.sprite.Sprite):
    def __init__(self, x, y, surface, path_points, speed=1):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.path_points = path_points
        self.target_point_index = 1
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if self.target_point_index < len(self.path_points):
            target_x, target_y = self.path_points[self.target_point_index]
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            if distance > self.speed:
                direction = pygame.math.Vector2(dx, dy).normalize()
                self.rect.x += self.speed * direction.x
                self.rect.y += self.speed * direction.y
            else:
                self.target_point_index += 1
        else:
            self.kill()

def spawn_random_pedestrian(paths, pedestrian_sprites, pedestrian_images):
    if not paths:
        return
    path = random.choice(paths)
    direction_forward = random.choice([True, False])
    if direction_forward:
        start_x, start_y = path[0]
        path_points = path
    else:
        start_x, start_y = path[-1]
        path_points = path[::-1]
    image = random.choice(pedestrian_images)
    pedestrian = Pedestrian(start_x, start_y, image, path_points)
    pedestrian_sprites.add(pedestrian)
