from enum import Enum, auto
import time
import json
from typing import List
from pathlib import Path
from pygame.math import Vector2
from enemy import Enemy
from character import Character
import random
import math
import threading
from collections import deque
from assets import create_asset
from loading_process import LoadingProgress
from logger import DifficultyLogger
from agentic_dda import generate_difficulty_score_with_request

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
        max_spawn_count: int,
        min_spawn_count: int,
        max_spawn_interval: float,
        min_spawn_interval: float,
        multipliers: dict[str, float]
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
        self.min_spawn_count = min_spawn_count
        self.max_spawn_count = max_spawn_count
        self.min_spawn_interval = min_spawn_interval
        self.max_spawn_interval = max_spawn_interval
        
        self.multipliers = multipliers

        

        # ---------- metrics ----------
        self.last_avg_enemy_distance = max_spawn_dist
        self.prev_avg_enemy_distance = None
        self.avg_distance_history: List[float] = []
        self.max_history_len = 5
        self.kill_count = 0
        self.enemy_count_delta = 0
        self.metric_history: deque[dict] = deque(maxlen=3)
        
        # ---------- difficulty system ----------
        self.difficulty_score = 0.5   # range [0, 1]
        self.target_difficulty = 0.5

        # time goal (0 = infinity)
        self.time_goal = 0.0
        
        self.far_time = 0.0
        self.close_time = 0.0



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

        self.logger = DifficultyLogger()
        # LLM async state
        self.llm_thread = None
        self.llm_busy = False
        self.latest_llm_score = 0.5   # fallback


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
        self.difficulty_score = 0.5
        self.target_difficulty = 0.5
        
        self.spawn_interval = self.default_spawn_interval
        self.spawn_count = self.default_spawn_count
        self.enemy_speed_range = self.default_enemy_speed_range
        self.min_spawn_dist = self.default_min_spawn_dist 
        self.max_spawn_dist = self.default_max_spawn_dist
        self.min_enemy_speed_limit = self.default_min_enemy_speed
        self.max_enemy_speed_limit = self.default_max_enemy_speed


        self.last_avg_enemy_distance = self.max_spawn_dist
        self.prev_avg_enemy_distance = None
        self.avg_distance_history.clear()

        self.last_spawn_enemy_count = 0
        self.current_enemy_count = 0
        self.enemy_count_delta = 0
        self.kill_count = 0
        self.metric_history.clear()
        


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
        
        
        normalized_state = self.get_normalized_state(
            player.shield_segments,
            player.max_shield_segments
        )
        
        self.metric_history.append(normalized_state)
        
        # 1. measure
        self._sample_avg_enemy_distance(player, enemies)
        avg_dist = self.last_avg_enemy_distance

        far_threshold = self.min_spawn_dist * 1.5
        close_threshold = self.min_spawn_dist * 1.5 # (you said "min spawn rate" but this should be distance)


        # FAR STATE
        if avg_dist > far_threshold:
            self.far_time += 1.0
        else:
            self.far_time = 0.0

        # CLOSE STATE
        if avg_dist < close_threshold:
            self.close_time += 1.0
        else:
            self.close_time = 0.0

        # 2. compute difficulty
        metric_factor = self._update_difficulty_from_metrics(player, normalized_state)
        if self.time_goal > 0:
            time_factor = self._update_difficulty_from_time() 
            metric_factor = 0.7 * metric_factor + 0.3 * time_factor
        else:
            metric_factor = metric_factor
        
        self.target_difficulty = metric_factor
        if self.player_profile["agent_dda"] == "LLM ON":
            # Only request if previous one finished
            if not self.llm_busy and len(self.metric_history) > 0:
                history_to_send = self.metric_history.copy()
                history_to_send.append(self.player_profile["mood"])  # include latest state
                self.metric_history.clear()

                self._request_llm_async(history_to_send)
                history_to_send.pop()
            self.target_difficulty = self.latest_llm_score
        # Always use latest available result
        # your final system (example hybrid)
        
        self.difficulty_score = self.target_difficulty
        # self.difficulty_score += (self.target_difficulty - self.difficulty_score) * 0.3
        self.difficulty_score = max(0.0, min(1.0, self.difficulty_score))

        # 4. APPLY difficulty
        self._apply_difficulty_to_enemy_speed()
        self._apply_difficulty_to_spawning()
        
        # 🔥 LOG EVERYTHING
        self.logger.log({
            "time": self.elapsed_time,
            "llm_score": self.latest_llm_score,
            "system_score": metric_factor,
            "target_difficulty": self.target_difficulty,
            "final_difficulty": self.difficulty_score
        })
        
        # 5. commentary (after everything updated)
        self.commentator.update({
            "avg_enemy_distance": self.last_avg_enemy_distance,
            "enemy_speed": self.enemy_speed_range[1],
            "spawn_count": self.spawn_count,
            "current_terrain": current_terrain,
            "lives_left": self.lives,
            "time_elapsed": self.elapsed_time,
            "time_goal": self.time_goal,
            "difficulty_score": self.difficulty_score,
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
    # Spawn logic
    # =========================================================

    def _spawn_tick(self, dt: float, player: Character, enemies: List[Enemy], world_objects=None):
        self.spawn_timer += dt
        if self.spawn_timer < self.spawn_interval:
            return

        self.spawn_timer -= self.spawn_interval

        self.current_enemy_count = len(enemies)
        self.enemy_count_delta = self.current_enemy_count - self.last_spawn_enemy_count

        for _ in range(self.spawn_count):
            enemies.append(self._spawn_enemy(player.pos, world_objects))

        self.last_spawn_enemy_count = len(enemies)


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

        world_objects.spawn_collectible(
            pos,
            difficulty_score=self.difficulty_score
        )
        
    def _adjust_multipliers_based_on_mood(self):
        if self.player_profile: 
            match self.player_profile["mood"]:
                case "Chill":
                    self.multipliers = map(lambda x: x * 0.8, self.multipliers)
                case "Neutral":
                    pass
                case "Focused":
                    self.multipliers = map(lambda x: x * 1.2, self.multipliers)
    
    def _update_difficulty_from_metrics(self, player: Character, state):
        self._adjust_multipliers_based_on_mood()

        # -----------------------------
        # NORMALIZED INPUTS (reuse LLM state)
        # -----------------------------
        health = state["player_state"]["health_pressure"]
        kill_rate = state["player_state"]["kill_pressure"]
        shield = state["player_state"]["shield_pressure"]

        density = state["environment_state"]["enemy_density"]
        safety = state["environment_state"]["distance_pressure"]

        close = state["environment_state"]["distance_state"]["close_score"]

        # -----------------------------
        # INTERPRETATION (VERY IMPORTANT)
        # -----------------------------
        # High values = player doing well → increase difficulty

        player_skill = (
            0.4 * kill_rate +
            0.3 * health +
            0.3 * shield
        )

        control_state = (
            0.5 * safety +   # far = safe
            0.5 * (1 - density)  # fewer enemies = safe
        )

        # behavioral signals (time-based)
        positioning = (
            0.6 * (1 - safety) +      # player escaping → too easy
            0.4 * (1 - close)  # not under pressure
        )

        # -----------------------------
        # FINAL METRIC SCORE
        # -----------------------------
        score = (
            0.5 * player_skill +
            0.3 * control_state +
            0.2 * positioning
        )

        # clamp to [0,1]
        return max(0.0, min(1.0, score))
    
    def _update_difficulty_from_time(self):
        if self.time_goal <= 0:
            return 0.0  # infinite mode

        progress = min(1.0, self.elapsed_time / self.time_goal)

        # nonlinear ramp (feels better than linear)
        return progress ** 2

    def _apply_difficulty_to_enemy_speed(self):
        base_min, base_max = self.default_enemy_speed_range

        factor = 0.5 + self.difficulty_score  # range ~[0.5 → 1.5]

        min_s = base_min * factor
        max_s = base_max * factor

        min_s = max(self.min_enemy_speed_limit, min(min_s, self.max_enemy_speed_limit))
        max_s = max(self.min_enemy_speed_limit, min(max_s, self.max_enemy_speed_limit))

        self.enemy_speed_range = (min_s, max_s)
        
    def _apply_difficulty_to_spawning(self):
        # more difficulty → more enemies, faster spawn
        self.spawn_count = int(
            self.default_spawn_count +
            self.difficulty_score * self.max_spawn_count
        )      
        self.spawn_interval = max(
            self.min_spawn_interval,
            self.default_spawn_interval * (1.2 - self.difficulty_score)
        )
     
    def get_normalized_state(self, shield_segments=None, max_shield_segments=None):
        # -----------------------------
        # Time (harder as time progresses)
        # -----------------------------
        if self.time_goal > 0:
            time_progress = min(1.0, self.elapsed_time / self.time_goal)
        else:
            time_progress = 0.0

        # -----------------------------
        # Player state (invert → pressure)
        # -----------------------------
        health_ratio = self.lives / self.initial_lives
        health_pressure = 1.0 - health_ratio

        if shield_segments is not None:
            shield_ratio = shield_segments / max_shield_segments
        else:
            shield_ratio = 0.5

        shield_pressure = 1.0 - shield_ratio

        # -----------------------------
        # Kill rate (invert → struggling)
        # -----------------------------
        raw_kill_rate = self.kill_count / (self.elapsed_time + 1e-5)
        kill_rate_norm = min(1.0, raw_kill_rate / 1.0)
        kill_pressure = 1.0 - kill_rate_norm

        # -----------------------------
        # Enemy density (more = harder)
        # -----------------------------
        enemy_density = min(1.0, self.current_enemy_count / 40)

        # -----------------------------
        # Distance (closer = harder)
        # -----------------------------
        min_dist = self.min_spawn_dist * 2.5
        distance_pressure = max(
            0.0,
            1.0 - min(1.0, self.last_avg_enemy_distance / min_dist)
        )

        # -----------------------------
        # Distance trend (KEEP AS IS)
        # -----------------------------
        MAX_TIME = 5

        close_score = min(1.0, self.close_time / MAX_TIME)  # close → hard

        # -----------------------------
        # Overall pressure (aggregated signal)
        # -----------------------------
        overall_pressure = (
            0.25 * health_pressure +
            0.10 * kill_pressure +
            0.15 * shield_pressure +
            0.40 * enemy_density +
            0.10 * distance_pressure
        )
        
        # -----------------------------
        # Clamp
        # -----------------------------
        def clamp(x):
            return max(0.0, min(1.0, x))

        normalized = {
            "current_difficulty": clamp(self.difficulty_score),
            "time_pressure": clamp(time_progress),

            "player_state": {
                "health_pressure": clamp(health_pressure),
                "kill_pressure": clamp(kill_pressure),
                "shield_pressure": clamp(shield_pressure)
            },

            "environment_state": {
                "enemy_density": clamp(enemy_density),
                "distance_pressure": clamp(distance_pressure),

                "distance_state": {
                    "close_score": clamp(close_score)  # high = hard
                }
            },
            "overall": {
                "pressure": clamp(overall_pressure)
            }
        }

        return normalized

    def _request_llm_async(self, normalized_state):
        def worker():
            try:
                result = generate_difficulty_score_with_request(normalized_state)
                if isinstance(result, float):
                    self.latest_llm_score = result
            except Exception as e:
                print("LLM async error:", e)
            finally:
                self.llm_busy = False

        self.llm_busy = True
        self.llm_thread = threading.Thread(target=worker, daemon=True)
        self.llm_thread.start()