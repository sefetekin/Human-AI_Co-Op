import math
import random
import pygame
from pygame.math import Vector2
from typing import List

from comment_manager import CommentaryManager
from config import GameConfig
from character import Character
from enemy import Enemy
from game_manager import GameManager, GameState
from render_world import WorldRenderer
from hud import HUDRenderer
from scoreboard import Scoreboard
from player_setup_ui import PlayerSetupUI
from scoreboard_renderer import ScoreboardRenderer


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
pygame.display.set_caption("Adaptive Survival Game")
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

hud_renderer = HUDRenderer(SCREEN_SIZE)
scoreboard = Scoreboard()
scoreboard_renderer = ScoreboardRenderer(SCREEN_SIZE)
setup_ui = PlayerSetupUI(SCREEN_SIZE)

# ---------- Game objects ----------
player = make_player(config)
enemies: List[Enemy] = []
final_time = None
current_entry = None

running = True


# --------------------
# Main loop
# --------------------
while running:
    dt = clock.tick(FPS) / 1000.0

    # ====================
    # Input
    # ====================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_manager.shutting_down = True
            if hasattr(game_manager, "asset_processes"):
                for p in game_manager.asset_processes:
                    if p.poll() is None:
                        p.terminate()

            running = False


        # ---------- PLAYER SETUP ----------
        if game_manager.state == GameState.PLAYER_SETUP:
            setup_ui.handle_event(event)
            hud_renderer.handle_event(event, game_manager)

            if setup_ui.start_requested:
                game_manager.player_profile = setup_ui.get_profile()
                
                game_manager.commentator = CommentaryManager(
                    traits=game_manager.player_profile,
                    llm_func="request",
                )
                if game_manager.player_profile["captions"] == "Caption OFF":
                    game_manager.commentator.enabled = False

                setup_ui.start_requested = False

                if game_manager.player_profile["content_generation"] == "Gen ON":
                    # ✅ run asset generation
                    game_manager.start_loading()
                else:
                    # ✅ skip generation but still move forward cleanly
                    background_objects = []
                    game_manager.loading_done = True
                    game_manager.state = GameState.LOADING

        # ---------- GAME OVER ----------
        elif game_manager.state == GameState.GAME_OVER:
            hud_renderer.handle_event(event, game_manager)

        # ---------- SCOREBOARD ----------
        elif game_manager.state == GameState.SCOREBOARD:
            scoreboard_renderer.handle_event(event)

    # ====================
    # Update
    # ====================
    
    if game_manager.state == GameState.LOADING:
        # Loading runs in background thread
        game_manager.tick(dt, None, None, "")
        if game_manager.state == GameState.PLAYING:
            # Loading finished, initialize game objects
            world_renderer = WorldRenderer(
                content_generation=game_manager.player_profile["content_generation"]
            )

    elif game_manager.state == GameState.PLAYING:
        keys = pygame.key.get_pressed()
        player.update(dt, world_renderer.world_objects, keys)
        
        for c in world_renderer.world_objects.collectibles[:]:
            if c.collides_with_player(player):
                if c.type.name == "HEART":
                    game_manager.lives = min(
                        game_manager.initial_lives,
                        game_manager.lives + 1
                    )
                elif c.type.name == "SHIELD":
                    player.shield_segments += 1
                elif c.type.name == "BROKEN_SHIELD":
                    player.shield_segments = max(0, player.shield_segments - 1)
                elif c.type.name == "LIGHTNING":
                    player.speed *= 1.25
                elif c.type.name == "TRAP":
                    player.speed *= 0.75
                world_renderer.world_objects.collectibles.remove(c)

        for e in enemies:
            e.update(dt, player.pos, world_renderer.world_objects)


        # Shield kills
        killed = player.kill_enemies(enemies)
        for k in killed:
            enemies.remove(k)
            game_manager.kill_count += 1

        # Core game logic (spawning, difficulty, death)
        game_manager.tick(dt, player, enemies, 
                          world_renderer.get_terrain_at_world_pos(player.pos),
                          world_renderer.world_objects)

        # Death transition
        if game_manager.state == GameState.GAME_OVER:
            final_time = game_manager.elapsed_time
            current_entry = scoreboard.add_score(
                name=game_manager.player_profile["name"],
                age_group=game_manager.player_profile["age_group"],
                mood=game_manager.player_profile["mood"],
                likes=game_manager.player_profile["likes"],
                time_survived=final_time,
                kills=game_manager.kill_count,
            )

    


    # ====================
    # Navigation / buttons
    # ====================

    # ---- GAME OVER buttons ----
    if game_manager.state == GameState.GAME_OVER:
        selected = hud_renderer.game_over_buttons.selected

        if selected == "Restart":
            hud_renderer.game_over_buttons.selected = None

            player = make_player(config)
            enemies.clear()
            final_time = None
            current_entry = None

            game_manager.reset()
            game_manager.state = GameState.PLAYING

        elif selected == "New Player":
            hud_renderer.game_over_buttons.selected = None

            player = make_player(config)
            enemies.clear()
            final_time = None
            current_entry = None

            setup_ui.reset()
            game_manager.reset()
            game_manager.state = GameState.PLAYER_SETUP

        elif selected == "Scoreboard":
            hud_renderer.game_over_buttons.selected = None
            game_manager.prev_state = GameState.GAME_OVER
            game_manager.state = GameState.SCOREBOARD

    # ---- PLAYER SETUP Scoreboard button ----
    if game_manager.state == GameState.PLAYER_SETUP:
        if hud_renderer.scoreboard_button.selected == "Scoreboard":
            hud_renderer.scoreboard_button.selected = None
            game_manager.prev_state = GameState.PLAYER_SETUP
            game_manager.state = GameState.SCOREBOARD

    # ---- SCOREBOARD back button ----
    if game_manager.state == GameState.SCOREBOARD:
        if scoreboard_renderer.back_requested:
            scoreboard_renderer.back_requested = False
            game_manager.state = game_manager.prev_state
            game_manager.prev_state = None


    # ====================
    # Render
    # ====================
    if game_manager.state == GameState.PLAYER_SETUP:
        hud_renderer.draw_player_setup(screen, setup_ui)

    elif game_manager.state == GameState.LOADING:
        hud_renderer.draw_loading(
            screen,
            game_manager.loading_progress
        )

        if not game_manager.loading_thread.is_alive():
            game_manager.state = GameState.PLAYING

    elif game_manager.state == GameState.SCOREBOARD:
        entries = scoreboard.get_entries()
        scoreboard_renderer.draw(screen, entries)

    else:
        world_renderer.draw(screen, player, enemies, dt)
        hud_renderer.draw(
            screen,
            game_manager,
            final_time,
            player
        )


    pygame.display.flip()

pygame.quit()
