from enum import Enum
from typing import List
from pygame.math import Vector2
from enemy import Enemy
from character import Character
import random
import math


class GameState(Enum):
    PLAYING = 1
    AWAITING_NAME = 2
    GAME_OVER = 3



class GameManager:
    def __init__(
        self,
        initial_lives: int,
        spawn_interval: float,
        spawn_count: int,
        min_spawn_dist: float,
        max_spawn_dist: float,
        enemy_speed_range: tuple[float, float],
    ):
        # ---------- game state ----------
        self.state = GameState.PLAYING

        # ---------- lives ----------
        self.initial_lives = initial_lives
        self.lives = initial_lives

        # ---------- timing ----------
        self.elapsed_time = 0.0
        self.second_timer = 0.0
        self.spawn_timer = 0.0

        # ---------- spawning ----------
        self.spawn_interval = spawn_interval
        self.spawn_count = spawn_count
        self.min_spawn_dist = min_spawn_dist
        self.max_spawn_dist = max_spawn_dist

        # defaults
        self.default_spawn_interval = spawn_interval
        self.default_spawn_count = spawn_count

        # bounds
        self.min_spawn_count = 3
        self.max_spawn_count = 10
        self.min_spawn_interval = 3.0
        self.max_spawn_interval = 15.0

        # ---------- enemy speed ----------
        self.enemy_speed_range = enemy_speed_range
        self.min_enemy_speed_limit = 30.0
        self.max_enemy_speed_limit = 300.0

        # ---------- metrics ----------
        self.last_avg_enemy_distance = 0.0
        self.prev_avg_enemy_distance = None
        self.avg_distance_history: List[float] = []
        self.max_history_len = 5
        self.kill_count = 0


        # ---------- spawn tracking ----------
        self.last_spawn_enemy_count = 0
        self.current_enemy_count = 0
        self.enemy_count_delta = 0

        # ---------- reference ----------
        self.shield_radius = None

    # =========================================================
    # Public API
    # =========================================================

    def reset(self):
        self.state = GameState.PLAYING
        self.lives = self.initial_lives

        self.elapsed_time = 0.0
        self.second_timer = 0.0
        self.spawn_timer = 0.0

        self.spawn_interval = self.default_spawn_interval
        self.spawn_count = self.default_spawn_count

        self.last_avg_enemy_distance = 0.0
        self.prev_avg_enemy_distance = None
        self.avg_distance_history.clear()

        self.last_spawn_enemy_count = 0
        self.current_enemy_count = 0
        self.enemy_count_delta = 0
        self.kill_count = 0


    def tick(self, dt: float, player: Character, enemies: List[Enemy]):
        if self.state != GameState.PLAYING:
            return

        self.elapsed_time += dt

        self._second_tick(dt, player, enemies)
        self._spawn_tick(dt, player, enemies)
        self._death_check(player, enemies)

    # =========================================================
    # Per-second logic
    # =========================================================

    def _second_tick(self, dt: float, player: Character, enemies: List[Enemy]):
        self.second_timer += dt
        if self.second_timer < 1.0:
            return

        self.second_timer -= 1.0

        if self.shield_radius is None:
            self.shield_radius = player.shield_radius

        self._sample_avg_enemy_distance(player, enemies)
        self._adjust_enemy_speed_from_distance()

    def _sample_avg_enemy_distance(self, player: Character, enemies: List[Enemy]):
        if not enemies:
            avg = 0.0
        else:
            total = 0.0
            for e in enemies:
                total += (e.pos - player.pos).length()
            avg = total / len(enemies)

        self.last_avg_enemy_distance = avg
        self.avg_distance_history.append(avg)
        if len(self.avg_distance_history) > self.max_history_len:
            self.avg_distance_history.pop(0)

    # =========================================================
    # Enemy speed control
    # =========================================================

    def _adjust_enemy_speed_from_distance(self):
        curr = self.last_avg_enemy_distance

        if self.prev_avg_enemy_distance is None:
            self.prev_avg_enemy_distance = curr
            return

        delta = curr - self.prev_avg_enemy_distance
        speed_changed = False

        # rate-of-change
        if delta > self.shield_radius:
            self._scale_enemy_speed(1.1)
            speed_changed = True
        elif delta < -self.shield_radius:
            self._scale_enemy_speed(1 / 1.1)
            speed_changed = True

        # absolute distance
        if not speed_changed:
            if curr > self.max_spawn_dist:
                self._scale_enemy_speed(1.1)
            elif curr < self.min_spawn_dist:
                self._scale_enemy_speed(1 / 1.1)

        self.prev_avg_enemy_distance = curr

    def _scale_enemy_speed(self, factor: float):
        min_s, max_s = self.enemy_speed_range

        min_s = max(self.min_enemy_speed_limit,
                    min(min_s * factor, self.max_enemy_speed_limit))
        max_s = max(self.min_enemy_speed_limit,
                    min(max_s * factor, self.max_enemy_speed_limit))

        self.enemy_speed_range = (min_s, max_s)

    # =========================================================
    # Spawn logic
    # =========================================================

    def _spawn_tick(self, dt: float, player: Character, enemies: List[Enemy]):
        self.spawn_timer += dt
        if self.spawn_timer < self.spawn_interval:
            return

        self.spawn_timer -= self.spawn_interval

        # track enemy count before spawning
        self.current_enemy_count = len(enemies)
        self.enemy_count_delta = (
            self.current_enemy_count - self.last_spawn_enemy_count
        )

        # baseline reversion
        self._revert_towards_default()

        ideal_delta = -self.spawn_interval / 2.0

        if self.enemy_count_delta < ideal_delta:
            if self.spawn_count < self.max_spawn_count:
                self.spawn_count += 1
            else:
                self.spawn_interval *= 0.9

        elif self.enemy_count_delta > ideal_delta:
            if self.spawn_count > self.min_spawn_count:
                self.spawn_count -= 1
            else:
                self.spawn_interval *= 1.1

        self.spawn_interval = max(
            self.min_spawn_interval,
            min(self.spawn_interval, self.max_spawn_interval),
        )

        for _ in range(self.spawn_count):
            enemies.append(self._spawn_enemy(player.pos))

        self.last_spawn_enemy_count = len(enemies)

    def _revert_towards_default(self):
        if self.spawn_count > self.default_spawn_count:
            self.spawn_count -= 1
        elif self.spawn_count < self.default_spawn_count:
            self.spawn_count += 1

        if self.spawn_interval > self.default_spawn_interval:
            self.spawn_interval *= 0.95
        elif self.spawn_interval < self.default_spawn_interval:
            self.spawn_interval *= 1.05

    # =========================================================
    # Death & helpers
    # =========================================================

    def _death_check(self, player: Character, enemies: List[Enemy]):
        for e in enemies:
            if (e.pos - player.pos).length_squared() <= (
                e.radius + player.player_radius
            ) ** 2:
                self.lives -= 1
                enemies.remove(e)
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                return

    def _spawn_enemy(self, player_pos: Vector2) -> Enemy:
        angle = random.random() * math.tau
        dist = random.uniform(self.min_spawn_dist, self.max_spawn_dist)

        pos = Vector2(
            player_pos.x + math.cos(angle) * dist,
            player_pos.y + math.sin(angle) * dist,
        )

        speed = random.uniform(*self.enemy_speed_range)
        return Enemy(pos, speed=speed)
