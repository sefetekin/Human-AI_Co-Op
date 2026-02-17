import pygame
from pygame.math import Vector2


class Enemy:
    def __init__(self, pos, speed: float = 80.0):
        self.pos = Vector2(pos)
        self.speed = speed
        self.radius = 12

        self.direction = "down"
        self.current_frame = 0
        self.animation_timer = 0
        # -------- LOAD SPRITE SHEET --------
        self.sheet = pygame.image.load(
            "assets/enemy_walk.png"
        ).convert_alpha()

        # -------- FRAME SIZE (ONE TILE SIZE) --------
        sheet_width, sheet_height = self.sheet.get_size()

        self.frame_w = sheet_width // 4
        self.frame_h = sheet_height // 4


        self.animations = {}
        self.load_animations()
        self.image = self.animations["down"][0]

    def load_animations(self):

        self.animations = {
            "down": [],
            "up": [],
            "left": [],
            "right": []
        }

        direction_cols = {
            "down": 0,
            "up": 1,
            "left": 2,
            "right": 3
        }

        for direction, col in direction_cols.items():

            for row in range(4):   # 4 frames per animation

                rect = pygame.Rect(
                    col * self.frame_w,   # direction
                    row * self.frame_h,   # animation frame
                    self.frame_w,
                    self.frame_h
                )

                frame = self.sheet.subsurface(rect)

                frame = pygame.transform.smoothscale(
                    frame,
                    (self.radius * 2, self.radius * 2)
                )

                self.animations[direction].append(frame)


    def update(self, dt: float, target_pos: Vector2, world_objects):

        dir = Vector2(target_pos) - self.pos
        dist = dir.length()

        if dist > 0:
            move_dist = min(self.speed * dt, dist)
            dir = dir.normalize()
            delta = dir * move_dist

            self._try_move(delta, world_objects)


            # -------- Direction Detection --------
            if abs(dir.x) > abs(dir.y):
                if dir.x > 0:
                    self.direction = "right"
                else:
                    self.direction = "left"
            else:
                if dir.y > 0:
                    self.direction = "down"
                else:
                    self.direction = "up"

        self.update_animation(dt)

    def update_animation(self, dt):

        self.animation_timer += dt

        if self.animation_timer >= 0.12:
            self.animation_timer = 0
            self.current_frame = (
                self.current_frame + 1
            ) % 4

        self.image = self.animations[self.direction][self.current_frame]



    def draw(self, surf, to_screen):

        p = to_screen(self.pos)
        offset = Vector2(self.image.get_size()) / 2
        surf.blit(self.image, p - offset)
    
    def _try_move(self, delta: Vector2, world_objects):

        # ---------- try original ----------
        new_pos = self.pos + delta
        if not world_objects.collides_circle(new_pos, self.radius):
            self.pos = new_pos
            return


        # ---------- try sliding ----------
        slide = Vector2(delta.x, 0)
        new_pos = self.pos + slide
        if slide.length_squared() > 0 and not world_objects.collides_circle(new_pos, self.radius):
            self.pos = new_pos
            return

        slide = Vector2(0, delta.y)
        new_pos = self.pos + slide
        if slide.length_squared() > 0 and not world_objects.collides_circle(new_pos, self.radius):
            self.pos = new_pos
            return


        # ---------- try perpendicular ----------
        perp = Vector2(-delta.y, delta.x) * 0.7
        new_pos = self.pos + perp
        if not world_objects.collides_circle(new_pos, self.radius):
            self.pos = new_pos
            return

        perp = Vector2(delta.y, -delta.x) * 0.7
        new_pos = self.pos + perp
        if not world_objects.collides_circle(new_pos, self.radius):
            self.pos = new_pos
            return

