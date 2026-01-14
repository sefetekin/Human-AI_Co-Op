import pygame
from game_manager import GameState


class HUDRenderer:
    def __init__(self, screen_size):
        self.screen_w, self.screen_h = screen_size
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_large = pygame.font.SysFont(None, 72)

        self.button_w = 160
        self.button_h = 48

    # =========================================================
    # Public
    # =========================================================

    def draw(self, screen, game_manager, final_time, player, scoreboard, name_input):
        # lives should always be visible
        self._draw_lives(screen, game_manager)

        self._draw_time(screen, game_manager, final_time)

        if game_manager.state == GameState.AWAITING_NAME:
            self._draw_game_over(screen)
            self._draw_name_input(screen, name_input)
            return

        if game_manager.state == GameState.GAME_OVER:
            self._draw_game_over(screen)
            self._draw_scoreboard(screen, scoreboard.get_scores())

        self._draw_debug_panel(screen, game_manager, player)

    # =========================================================
    # Core HUD
    # =========================================================

    def _draw_time(self, screen, game_manager, final_time):
        t = final_time if final_time is not None else game_manager.elapsed_time
        mins = int(t // 60)
        secs = int(t % 60)
        txt = self.font_small.render(
            f"{mins:02d}:{secs:02d}", True, (220, 220, 220)
        )
        screen.blit(txt, (self.screen_w - 80, 10))

    # =========================================================
    # Lives (FIXED)
    # =========================================================

    def _draw_lives(self, screen, game_manager):
        lives = game_manager.lives
        max_lives = game_manager.initial_lives

        heart_radius = 8
        spacing = 28
        total_w = (max_lives - 1) * spacing
        cx = self.screen_w // 2
        y = 28

        for i in range(max_lives):
            x = cx - total_w // 2 + i * spacing
            filled = i < lives
            self._draw_heart(
                screen,
                (int(x), y),
                heart_radius * 2,
                (220, 60, 60),
                filled,
            )

    def _draw_heart(self, surface, center, size, color, filled=True):
        w = max(6, int(size))
        s = pygame.Surface((w, w), pygame.SRCALPHA)
        cx = w / 2
        cy = w / 2
        r = w * 0.25

        left = (cx - r, cy - r * 0.6)
        right = (cx + r, cy - r * 0.6)
        poly = [
            (cx - r * 1.4, cy),
            (cx, cy + r * 1.35),
            (cx + r * 1.4, cy),
        ]

        if filled:
            pygame.draw.circle(s, color, left, r)
            pygame.draw.circle(s, color, right, r)
            pygame.draw.polygon(s, color, poly)
        else:
            thickness = max(1, int(w * 0.12))
            pygame.draw.circle(s, color, left, r, thickness)
            pygame.draw.circle(s, color, right, r, thickness)
            pygame.draw.polygon(s, color, poly, thickness)

        surface.blit(
            s,
            (int(center[0] - w / 2), int(center[1] - w / 2)),
        )

    # =========================================================
    # Game over + restart
    # =========================================================

    def _draw_game_over(self, screen):
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = self.font_large.render("GAME OVER", True, (240, 80, 80))
        screen.blit(
            title,
            (
                self.screen_w // 2 - title.get_width() // 2,
                self.screen_h // 2 - 150,
            ),
        )

        self._draw_restart_button(screen)

    def _draw_restart_button(self, screen):
        bx = self.screen_w // 2 - self.button_w // 2
        by = self.screen_h // 2 + 40

        pygame.draw.rect(
            screen,
            (200, 200, 200),
            pygame.Rect(bx, by, self.button_w, self.button_h),
            border_radius=6,
        )

        txt = self.font_small.render("Restart", True, (20, 20, 20))
        screen.blit(
            txt,
            (
                bx + self.button_w // 2 - txt.get_width() // 2,
                by + self.button_h // 2 - txt.get_height() // 2,
            ),
        )

    # =========================================================
    # Name input (FIXED POSITION)
    # =========================================================

    def _draw_name_input(self, screen, name_text):
        x = self.screen_w // 2
        y = self.screen_h // 2 - 40   # ⬅ moved UP

        prompt = self.font_small.render(
            "Enter your name:", True, (220, 220, 220)
        )
        screen.blit(prompt, (x - prompt.get_width() // 2, y))

        box_w, box_h = 240, 36
        bx = x - box_w // 2
        by = y + 30

        pygame.draw.rect(
            screen, (255, 255, 255), (bx, by, box_w, box_h), 2
        )

        name_surf = self.font_small.render(name_text, True, (255, 255, 255))
        screen.blit(
            name_surf,
            (bx + 10, by + box_h // 2 - name_surf.get_height() // 2),
        )

    # =========================================================
    # Scoreboard
    # =========================================================

    def _draw_scoreboard(self, screen, scores):
        x = self.screen_w // 2
        y = self.screen_h // 2 + 110
        line_h = 20

        title = self.font_small.render("Top Runs", True, (220, 220, 220))
        screen.blit(title, (x - title.get_width() // 2, y))

        for i, entry in enumerate(scores):
            mins = int(entry["time"] // 60)
            secs = int(entry["time"] % 60)
            txt = self.font_small.render(
                f"{i+1}. {entry['name']} — {mins:02d}:{secs:02d}  |  Kills: {entry['kills']}"
,
                True,
                (200, 200, 200),
            )
            screen.blit(
                txt,
                (x - txt.get_width() // 2, y + 22 + i * line_h),
            )

    # =========================================================
    # Debug panel
    # =========================================================

    def _draw_debug_panel(self, screen, game_manager, player):
        x = self.screen_w - 230
        y = self.screen_h // 2 - 120
        line_h = 22

        min_speed, max_speed = game_manager.enemy_speed_range
        delta = game_manager.enemy_count_delta

        delta_color = (220, 220, 220)
        if delta > 0:
            delta_color = (120, 240, 120)
        elif delta < 0:
            delta_color = (240, 120, 120)

        lines = [
            ("Spawn Count", f"{game_manager.spawn_count}", (220, 220, 220)),
            ("Spawn Interval", f"{game_manager.spawn_interval:.2f}s", (220, 220, 220)),
            ("Shield Count", f"{player.shield_segments}", (220, 220, 220)),
            ("Avg Distance", f"{game_manager.last_avg_enemy_distance:.1f}", (220, 220, 220)),
            ("Enemy Δ", f"{delta}", delta_color),
            ("Enemy Min Speed", f"{min_speed:.1f}", (220, 220, 220)),
            ("Enemy Max Speed", f"{max_speed:.1f}", (220, 220, 220)),
        ]

        panel_h = line_h * len(lines) + 10
        panel = pygame.Surface((215, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        screen.blit(panel, (x - 10, y - 5))

        for i, (label, value, color) in enumerate(lines):
            surf = self.font_small.render(f"{label}: {value}", True, color)
            screen.blit(surf, (x, y + i * line_h))
