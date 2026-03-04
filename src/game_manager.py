from enum import Enum, auto
import time
from typing import List
from pathlib import Path
from pygame.math import Vector2
from enemy import Enemy
from character import Character
import random
import math
import threading
from assets import create_asset
from comment_manager import CommentaryManager
from loading_process import LoadingProgress

class GameState(Enum):
    PLAYER_SETUP = auto()
    LOADING = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    SCOREBOARD = auto()



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
        self.state = GameState.PLAYER_SETUP
        self.prev_state = None

        # ---------- lives ----------
        self.initial_lives = initial_lives
        self.lives = initial_lives

        # ---------- timing ----------
        self.elapsed_time = 0.0
        self.second_timer = 0.0
        self.spawn_timer = 4.0

        # ---------- spawning ----------
        self.spawn_interval = spawn_interval
        self.spawn_count = spawn_count
        self.min_spawn_dist = min_spawn_dist
        self.max_spawn_dist = max_spawn_dist


        # ---------- enemy speed ----------
        self.enemy_speed_range = enemy_speed_range
        self.min_enemy_speed_limit = 30.0
        self.max_enemy_speed_limit = 300.0
        
        
        # defaults
        self.default_spawn_interval = spawn_interval
        self.default_spawn_count = spawn_count
        self.default_enemy_speed_range = enemy_speed_range
        self.default_min_spawn_dist = min_spawn_dist
        self.default_max_spawn_dist = max_spawn_dist
        self.default_min_enemy_speed = self.min_enemy_speed_limit
        self.default_max_enemy_speed = self.max_enemy_speed_limit

        # bounds
        self.min_spawn_count = 3
        self.max_spawn_count = 10
        self.min_spawn_interval = 3.0
        self.max_spawn_interval = 15.0

        

        # ---------- metrics ----------
        self.last_avg_enemy_distance = 0.0
        self.prev_avg_enemy_distance = None
        self.avg_distance_history: List[float] = []
        self.max_history_len = 5
        self.kill_count = 0
        self.enemy_count_delta = 0
        self.last_avg_enemy_distance = 0.0



        # ---------- spawn tracking ----------
        self.last_spawn_enemy_count = 0
        self.current_enemy_count = 0
        self.enemy_count_delta = 0
        
        self.collectible_spawn_min = 5.0
        self.collectible_spawn_max = 12.0
        self.collectible_spawn_timer = random.uniform(
            self.collectible_spawn_min,
            self.collectible_spawn_max
        )

        # ---------- reference ----------
        self.shield_radius = None
        
        # ---------- pre-game ----------
        self.player_profile = None
        self.loading_done = False

        self.commentator = None
        self.loading_progress = LoadingProgress()
        self.shutting_down = False




    # =========================================================
    # Public API
    # =========================================================

    def reset(self):
        self.state = GameState.PLAYING
        if self.commentator and self.player_profile["captions"] == "Caption ON":
            self.commentator.enabled = True
        self.lives = self.initial_lives

        self.elapsed_time = 0.0
        self.second_timer = 0.0
        self.spawn_timer = 4.0

        self.spawn_interval = self.default_spawn_interval
        self.spawn_count = self.default_spawn_count
        self.enemy_speed_range = self.default_enemy_speed_range
        self.min_spawn_dist = self.default_min_spawn_dist 
        self.max_spawn_dist = self.default_max_spawn_dist
        self.min_enemy_speed_limit = self.default_min_enemy_speed
        self.max_enemy_speed_limit = self.default_max_enemy_speed


        self.last_avg_enemy_distance = 0.0
        self.prev_avg_enemy_distance = None
        self.avg_distance_history.clear()

        self.last_spawn_enemy_count = 0
        self.current_enemy_count = 0
        self.enemy_count_delta = 0
        self.kill_count = 0


    def tick(self, dt: float, player: Character, enemies: List[Enemy], current_terrain: str, world_objects=None):
        # ---------- LOADING ----------
        if self.state == GameState.LOADING:
            if self.loading_done:
                self.loading_done = False
                self.state = GameState.PLAYING
                if self.commentator and self.player_profile["captions"] == "Caption ON":
                    self.commentator.enabled = True
                self.reset()
            return
        
        # ---------- PLAYING ----------
        if self.state != GameState.PLAYING:
            return

        self.elapsed_time += dt
        
        self._second_tick(dt, player, enemies, current_terrain)
        self._spawn_tick(dt, player, enemies, world_objects)
        self._collectible_spawn_tick(dt, player, world_objects)
        self._death_check(player, enemies)

    


    # =========================================================
    # Per-second logic
    # =========================================================

    def _second_tick(self, dt: float, player: Character, enemies: List[Enemy], current_terrain: str):
        self.second_timer += dt
        if self.second_timer < 1.0:
            return

        self.second_timer -= 1.0

        if self.shield_radius is None:
            self.shield_radius = player.shield_radius
    
        self._sample_avg_enemy_distance(player, enemies)
    
        self._adjust_enemy_speed_from_distance()
        self.commentator.update({
            "avg_enemy_distance": self.last_avg_enemy_distance,
            "enemy_speed": self.max_enemy_speed_limit,
            "spawn_count": self.spawn_count,
            "current_terrain": current_terrain,
            "lives_left": self.lives,
        })

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

    def _spawn_tick(self, dt: float, player: Character, enemies: List[Enemy], world_objects=None):
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
            enemies.append(self._spawn_enemy(player.pos, world_objects))

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
                    if self.commentator and self.player_profile["captions"] == "Caption ON":
                        self.commentator.enabled = False
                        self.commentator.current_line = ""
                        self.commentator.expire_time = 0
                self.commentator.trigger_event(
                    "LOST_LIFE",
                    {"lives_left": self.lives}
                )

                return

    def _spawn_enemy(self, player_pos: Vector2, world_objects) -> Enemy:
        angle = random.random() * math.tau
        dist = random.uniform(self.min_spawn_dist, self.max_spawn_dist)

        pos = Vector2(
            player_pos.x + math.cos(angle) * dist,
            player_pos.y + math.sin(angle) * dist,
        )

        speed = random.uniform(*self.enemy_speed_range)
        enemy = Enemy(pos, speed=speed)

        enemy.pos = world_objects.resolve_circle_penetration(
            enemy.pos,
            enemy.radius
        )

        return enemy

    
    def start_loading(self):
        if getattr(self, "loading_thread", None) and self.loading_thread.is_alive():
            return  # already loading

        
        self.state = GameState.LOADING
        self.loading_done = False
        self.clear_folder("../outputs")

        self.loading_thread = threading.Thread(
            target=self._run_loading,
            daemon=True,
        )
        self.loading_thread.start()


    def _run_loading(self):
        try:
            self._run_loading_scripts()
        finally:
            self.loading_done = True

    def _run_loading_scripts(self, multi_processing: bool = False):
        terrain_types = {
            "Rock": "rocky terrain of a mountain",
            #"Desert": "sand with hills and Tumbleweed",
            "Forest": "grassy ground of a forest",
        }
        input_types = {
            "dirt_with_stones": "small",
        }
        inputted_types = self.player_profile["background"]
        for t in inputted_types:
            if t not in terrain_types:
                terrain_types[t] = f"a ground full of {t}"
        total_assets = len(terrain_types) * len(input_types)
        self.loading_progress.set_total(total_assets)

        self.asset_processes = []

        # ---- start all processes ----
        for terrain, description in terrain_types.items():
            for input_type, output_type in input_types.items():
                self.loading_progress.advance(
                    0, f"{terrain} - {output_type}"
                )

                process = create_asset(
                    template_path=Path(f"templates/{input_type}.png"),
                    prompt_override=(
                        f"a low-contrast 2D Pixel Art game asset representing "
                        f"{description} texture from bird's eye view"
                    ),
                    output_path=Path(
                        f"outputs/{terrain.lower()}_{output_type}.jpg"
                    ),
                    radius=10,
                )

                self.asset_processes.append(process)
                
                if not multi_processing:
                    # Wait for current asset
                    while process.poll() is None:
                        if self.shutting_down:
                            process.terminate()
                            return
                        time.sleep(0.1)
                    self.loading_progress.advance(1)

        if multi_processing:
            for p in self.asset_processes:
                p.wait()
                self.loading_progress.advance(1)

    def clear_folder(self, path: str):
        from pathlib import Path
        import shutil

        folder = Path(path).resolve()

        if not folder.is_dir():
            raise ValueError("Path must be an existing directory")

        if len(folder.parts) <= 2:
            raise ValueError("Refusing to clear unsafe directory")

        shutil.rmtree(folder)
        folder.mkdir()
    
    def _collectible_spawn_tick(self, dt, player, world_objects):

        self.collectible_spawn_timer -= dt

        if self.collectible_spawn_timer > 0:
            return

        # reset timer
        self.collectible_spawn_timer = random.uniform(
            self.collectible_spawn_min,
            self.collectible_spawn_max
        )

        # spawn position around player
        angle = random.random() * math.tau
        dist = random.uniform(120, 350)

        pos = Vector2(
            player.pos.x + math.cos(angle) * dist,
            player.pos.y + math.sin(angle) * dist,
        )

        world_objects.spawn_collectible(pos)
