import math
import random
import pygame
from pygame.math import Vector2
from typing import List

from config import GameConfig
from character import Character
from enemy import Enemy
from game_manager import GameManager, GameState
from render_world import WorldRenderer
from hud import HUDRenderer
from scoreboard import Scoreboard   # NEW


# --------------------
# Engine config
# --------------------
SCREEN_SIZE = (800, 600)
FPS = 60
# --------------------


# ---------- Factories ----------

def make_player(config: GameConfig) -> Character:
    return Character(
        SCREEN_SIZE,
        pos=(0, 0),
        speed=config.player_speed,
        shield_radius=config.shield_radius,
        shield_segments=config.shield_segments,
        shield_orbit_speed=config.shield_orbit_speed,
        shield_orbit_ball_radius=config.shield_orbit_ball_radius,
    )


def random_spawn_position_around(
    center: Vector2,
    min_d: float,
    max_d: float,
) -> Vector2:
    angle = random.random() * math.tau
    dist = random.uniform(min_d, max_d)
    return Vector2(
        center.x + math.cos(angle) * dist,
        center.y + math.sin(angle) * dist,
    )


def make_enemies(
    config: GameConfig,
    count: int,
    player_pos: Vector2,
) -> List[Enemy]:
    enemies: List[Enemy] = []
    for _ in range(count):
        pos = random_spawn_position_around(
            player_pos,
            config.enemy_min_spawn_dist,
            config.enemy_max_spawn_dist,
        )
        speed = random.uniform(
            config.enemy_min_speed,
            config.enemy_max_speed,
        )
        enemies.append(Enemy(pos, speed=speed))
    return enemies


# --------------------
# Main
# --------------------
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()

# ---------- Config ----------
config = GameConfig()

# ---------- Systems ----------
game_manager = GameManager(
    initial_lives=config.initial_lives,
    spawn_interval=config.spawn_interval,
    spawn_count=config.spawn_count,
    min_spawn_dist=config.enemy_min_spawn_dist,
    max_spawn_dist=config.enemy_max_spawn_dist,
    enemy_speed_range=(
        config.enemy_min_speed,
        config.enemy_max_speed,
    ),
)

world_renderer = WorldRenderer()
hud_renderer = HUDRenderer(SCREEN_SIZE)
scoreboard = Scoreboard()   # NEW

# ---------- Game state ----------
player = make_player(config)
enemies = make_enemies(
    config,
    config.initial_enemy_count,
    player.pos,
)

final_time = None
player_name_input = ""      # NEW
running = True

BUTTON_W, BUTTON_H = 160, 48

# --------------------
# Main loop
# --------------------
while running:
    dt = clock.tick(FPS) / 1000.0

    # ---------- Input ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ----- name input -----
        if game_manager.state == GameState.AWAITING_NAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    scoreboard.add_score(
                        player_name_input,
                        final_time,
                        game_manager.kill_count,
                    )

                    player_name_input = ""
                    game_manager.state = GameState.GAME_OVER

                elif event.key == pygame.K_BACKSPACE:
                    player_name_input = player_name_input[:-1]

                else:
                    if len(player_name_input) < 12 and event.unicode.isprintable():
                        player_name_input += event.unicode

        # ----- restart button -----
        if game_manager.state == GameState.GAME_OVER:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                bx = SCREEN_SIZE[0] // 2 - BUTTON_W // 2
                by = SCREEN_SIZE[1] // 2 + 40
                if bx <= mx <= bx + BUTTON_W and by <= my <= by + BUTTON_H:
                    player = make_player(config)
                    enemies = make_enemies(
                        config,
                        config.initial_enemy_count,
                        player.pos,
                    )
                    game_manager.reset()
                    final_time = None
                    player_name_input = ""

    keys = pygame.key.get_pressed()

    # ---------- Update ----------
    if game_manager.state == GameState.PLAYING:
        player.update(dt, keys)

        for e in enemies:
            e.update(dt, player.pos)

        # shield kills
        killed = player.kill_enemies(enemies)
        for k in killed:
            enemies.remove(k)
            game_manager.kill_count += 1


        game_manager.tick(dt, player, enemies)

        # transition to name entry on death
        if game_manager.state == GameState.GAME_OVER:
            final_time = game_manager.elapsed_time
            game_manager.state = GameState.AWAITING_NAME

    else:
        if final_time is None:
            final_time = game_manager.elapsed_time

    # ---------- Render ----------
    world_renderer.draw(screen, player, enemies)
    hud_renderer.draw(
        screen,
        game_manager,
        final_time,
        player,
        scoreboard,
        player_name_input,
    )
    pygame.display.flip()

pygame.quit()
