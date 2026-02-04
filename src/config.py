from dataclasses import dataclass


@dataclass
class GameConfig:
    # --- player ---
    player_speed: float = 240.0
    player_radius: int = 12

    # --- shields ---
    shield_segments: int = 3
    shield_radius: float = 100.0
    shield_orbit_speed: float = 120.0
    shield_orbit_ball_radius: float = 10.0

    # --- enemies ---
    enemy_min_speed: float = 50.0
    enemy_max_speed: float = 100.0
    enemy_radius: int = 8

    # --- spawning ---
    initial_enemy_count: int = 6
    spawn_interval: float = 5.0
    spawn_count: int = 5
    enemy_min_spawn_dist: float = 150.0
    enemy_max_spawn_dist: float = 600.0

    # --- lives ---
    initial_lives: int = 2
