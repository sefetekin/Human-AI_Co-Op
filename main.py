import math
import random
import subprocess
import sys
import pygame
from pygame.math import Vector2
from typing import List, Tuple, Union
from character import Character
from enemy import Enemy
from assets import create_assets_for_all, create_asset
from pathlib import Path


# --------------------
# Configurable globals
# --------------------
SCREEN_SIZE = (800, 600)
INITIAL_SHIELD_SEGMENTS = 5
INITIAL_ENEMY_COUNT = 6

SHIELD_RADIUS = 100.0
SHIELD_ORBIT_SPEED = 120.0
SHIELD_ORBIT_BALL_RADIUS = 10.0

ENEMY_MIN_SPEED = 50.0
ENEMY_MAX_SPEED = 100.0
ENEMY_MIN_SPAWN_DIST = 150.0   # min distance from player spawn
ENEMY_MAX_SPAWN_DIST = 600.0   # max distance from player spawn

# Lives: initial global lives count (current lives is reset_game-managed)
lives = 2
initial_lives = lives
# --------------------

# Minimal demonstration when run directly
if __name__ == "__main__":
    # outs_all = create_assets_for_all(prompt_overrides={"all:": "A pencil sketch of a dog"}, radius=4)
    # outs_all_old = create_asset_old(input_image="templates/dog_1.jpg", prompt="A pencil sketch of a dog", radius=10)
    # print("Created assets old:", outs_all_old)
    # outs_all = create_asset(template_path=Path("templates/dog_1.jpg"), traits={"age":"23", "likes":"golden retrievers", "dislikes":"black dogs"}, output_path=Path("outputs/gpt_test2.jpg"), radius=15)
    outs_all = create_asset(template_path=Path("templates/test1.jpg"), prompt_override="A high quality scene from a movie captured by a professional camera. A very beautiful woman stands in a rugged cave-like environment with stone walls and patches of snow. She has an adventurous appearance, wearing a sleeveless top, shorts, gloves, and a utility belt, exuding a determined and alert expression as if ready to explore or face a challenge", output_path=Path("outputs/gpt_test2.jpg"), radius=100)
    print("Created assets:", outs_all)

    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()
    

    def make_player():
        return Character(
            SCREEN_SIZE,
            pos=(0, 0),
            shield_radius=SHIELD_RADIUS,
            shield_segments=INITIAL_SHIELD_SEGMENTS,
            shield_orbit_speed=SHIELD_ORBIT_SPEED,
            shield_orbit_ball_radius=SHIELD_ORBIT_BALL_RADIUS,
        )

    def random_spawn_position_around(center: Vector2,
                                     min_d: float, max_d: float) -> Vector2:
        angle = random.random() * math.tau
        dist = random.uniform(min_d, max_d)
        return Vector2(center.x + math.cos(angle) * dist, center.y
                       + math.sin(angle) * dist)

    def make_enemies(count: int, player_pos: Vector2):
        enemies = []
        for _ in range(count):
            pos = random_spawn_position_around(
                player_pos, ENEMY_MIN_SPAWN_DIST, ENEMY_MAX_SPAWN_DIST)
            speed = random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)
            enemies.append(Enemy(pos, speed=speed))
        return enemies

    # reset function - now also resets elapsed time, win state and lives
    def reset_game():
        global lives
        lives = initial_lives
        player = make_player()
        enemies = make_enemies(INITIAL_ENEMY_COUNT, player.pos)
        return player, enemies, False, False, 0.0

    player, enemies, game_over, game_won, elapsed_time = reset_game()
    final_time = None

    font_small = pygame.font.SysFont(None, 24)
    font_large = pygame.font.SysFont(None, 72)

    def check_player_hit(player: Character,
                         enemies: List[Enemy]) -> Union[Enemy, None]:
        # return the first enemy that touches the player
        # (so we can remove it and only count one hit)
        for e in enemies:
            if ((e.pos - player.pos).length_squared() <=
                    (e.radius + player.player_radius) ** 2):
                return e
        return None

    # restart button layout
    button_w, button_h = 160, 48

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if ((game_over or game_won)
                    and event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1):
                # check if clicked restart
                mx, my = event.pos
                bx = screen.get_width() // 2 - button_w // 2
                by = screen.get_height() // 2 + 40
                if bx <= mx <= bx + button_w and by <= my <= by + button_h:
                    player, enemies, game_over, \
                        game_won, elapsed_time = reset_game()
                    final_time = None

        keys = pygame.key.get_pressed()
        if not (game_over or game_won):
            player.update(dt, keys)

            for e in enemies:
                e.update(dt, player.pos)

            # increment elapsed time while playing
            elapsed_time += dt

            # check if any enemy touches player
            # -> decrement life and remove that enemy
            hit_enemy = check_player_hit(player, enemies)
            if hit_enemy is not None:
                # decrement global lives and remove the enemy
                # so repeated frames don't re-hit instantly
                lives -= 1
                try:
                    enemies.remove(hit_enemy)
                except ValueError:
                    pass

                if lives <= 0:
                    game_over = True
                    game_won = False
                    final_time = elapsed_time
            else:
                # only kill enemies with shields if game not over
                killed = player.kill_enemies(enemies)
                for k in killed:
                    try:
                        enemies.remove(k)
                    except ValueError:
                        pass

                # if all enemies killed -> win
                if len(enemies) == 0:
                    game_won = True
                    game_over = True
                    final_time = elapsed_time

        screen.fill((30, 30, 40))
        for e in enemies:
            e.draw(screen, player.world_to_screen)

        player.draw(screen)

        def draw_heart(surface: pygame.Surface,
                       center: Tuple[int, int], size: int,
                       color: Tuple[int, int, int], filled: bool = True):
            # create a small surface to draw a heart
            # (two circles + triangle/polygon)
            w = max(6, int(size))
            s = pygame.Surface((w, w), pygame.SRCALPHA)
            cx = w / 2.0
            cy = w / 2.0
            r = w * 0.25
            left = (cx - r, cy - r * 0.6)
            right = (cx + r, cy - r * 0.6)
            poly = [
                (cx - r * 1.4, cy),
                (cx, cy + r * 1.35),
                (cx + r * 1.4, cy),
            ]

            if filled:
                pygame.draw.circle(
                    s, color, (int(left[0]), int(left[1])), int(r))
                pygame.draw.circle(
                    s, color, (int(right[0]), int(right[1])), int(r))
                pygame.draw.polygon(
                    s, color, [(int(px), int(py)) for px, py in poly])
            else:
                thickness = max(1, int(w * 0.12))
                pygame.draw.circle(
                    s, color, (int(left[0]), int(left[1])), int(r), thickness)
                pygame.draw.circle(
                    s, color, (int(right[0]),
                               int(right[1])), int(r), thickness)
                pygame.draw.polygon(
                    s, color, [(int(px), int(py))
                               for px, py in poly], thickness)

            blit_pos = (int(center[0] - w / 2.0), int(center[1] - w / 2.0))
            surface.blit(s, blit_pos)

        # draw lives at top-center as hearts
        # (filled = remaining, hollow = lost)
        life_radius = 8
        spacing = 28
        total_w = (initial_lives - 1) * spacing  # distance across centers
        cx = screen.get_width() // 2
        top_y = 28
        heart_size = life_radius * 2  # tweak this to scale hearts
        for i in range(initial_lives):
            x = cx - total_w // 2 + i * spacing
            if i < lives:
                draw_heart(screen, (int(x), top_y), heart_size,
                           (220, 60, 60), filled=True)
            else:
                draw_heart(screen, (int(x), top_y), heart_size,
                           (220, 60, 60), filled=False)

        # elapsed time display at top-right during gameplay
        # (and when paused on end we still show final time below)
        display_time = elapsed_time if not final_time else final_time
        minutes = int(display_time // 60)
        seconds = int(display_time % 60)
        centis = int((display_time - int(display_time)) * 100)
        time_str = f"{minutes:02d}:{seconds:02d}.{centis:02d}"
        time_txt = font_small.render(time_str, True, (220, 220, 220))
        # top-right placement with margin
        margin = 10
        tx = screen.get_width() - time_txt.get_width() - margin
        ty = 8
        screen.blit(time_txt, (tx, ty))

        txt = font_small.render(
            f"Enemies: {len(enemies)}", True, (220, 220, 220))
        screen.blit(txt, (10, 10))

        if game_over:
            # dark overlay
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            if game_won:
                # you won text
                title_surf = font_large.render(
                    "YOU WON", True, (120, 240, 120))
            else:
                # game over text
                title_surf = font_large.render(
                    "GAME OVER", True, (240, 80, 80))

            gx = screen.get_width() // 2 - title_surf.get_width() // 2
            gy = screen.get_height() // 2 - title_surf.get_height() // 2 - 40
            screen.blit(title_surf, (gx, gy))

            # show final time on the end screen
            if final_time is not None:
                fm = int(final_time // 60)
                fs = int(final_time % 60)
                fc = int((final_time - int(final_time)) * 100)
                final_str = f"Time: {fm:02d}:{fs:02d}.{fc:02d}"
                final_surf = font_small.render(
                    final_str, True, (220, 220, 220))
                fx = screen.get_width() // 2 - final_surf.get_width() // 2
                fy = gy + title_surf.get_height() + 8
                screen.blit(final_surf, (fx, fy))

            # restart button
            bx = screen.get_width() // 2 - button_w // 2
            by = screen.get_height() // 2 + 40
            button_rect = pygame.Rect(bx, by, button_w, button_h)
            pygame.draw.rect(screen, (200, 200, 200),
                             button_rect, border_radius=6)
            txt_r = font_small.render("Restart", True, (20, 20, 20))
            txb = bx + button_w // 2 - txt_r.get_width() // 2
            tyb = by + button_h // 2 - txt_r.get_height() // 2
            screen.blit(txt_r, (txb, tyb))

        pygame.display.flip()

    pygame.quit()
