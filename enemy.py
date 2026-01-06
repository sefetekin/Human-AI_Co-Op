import pygame
from pygame.math import Vector2


class Enemy:
    def __init__(self, pos, speed: float = 80.0):
        self.pos = Vector2(pos)
        self.speed = speed
        self.color = (200, 50, 50)
        self.radius = 8

    def update(self, dt: float, target_pos: Vector2):
        dir = Vector2(target_pos) - self.pos
        dist = dir.length()
        if dist > 0:
            move_dist = min(self.speed * dt, dist)
            self.pos += dir / dist * move_dist

    def draw(self, surf, to_screen):
        p = to_screen(self.pos)
        pygame.draw.circle(
            surf, self.color, (int(p.x), int(p.y)), self.radius)
