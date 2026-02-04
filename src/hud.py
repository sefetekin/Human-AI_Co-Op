import pygame
from yfinance import screen
from game_manager import GameState
from ui.select_buttons import SelectButtons

class HUDRenderer:
    def __init__(self, screen_size):
        self.screen_w, self.screen_h = screen_size
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_large = pygame.font.SysFont(None, 72)

        self.button_w = 160
        self.button_h = 48
        cx = self.screen_w // 2
        y = self.screen_h // 2 + 40
        
        self.scoreboard_button = SelectButtons(
            [("Scoreboard", (self.screen_w - self.button_w - 20,  # top-right X
                20,                                   # top-right Y
                self.button_w,
                self.button_h,))]
        )

        self.game_over_buttons = SelectButtons([
            ("Restart", (cx - 240, y, 140, 44)),
            ("New Player", (cx - 70, y, 140, 44)),
            ("Scoreboard", (cx + 100, y, 140, 44)),
        ])

    # =========================================================
    # Public
    # =========================================================

    def draw(self, screen, game_manager, final_time, player):
        
        if game_manager.state in (GameState.PLAYER_SETUP, GameState.LOADING):
            return

        self._draw_lives(screen, game_manager)
        self._draw_time(screen, game_manager, final_time)

        if game_manager.state == GameState.GAME_OVER:
            self._draw_game_over(screen)
            self.game_over_buttons.draw(screen, self.font_small)



        self._draw_debug_panel(screen, game_manager, player)
        self.draw_commentary(
            screen,
            game_manager.commentator.get_line()
        )


    # =========================================================
    # PLAYER SETUP (DRAW ONLY)
    # =========================================================
    def draw_player_setup(self, screen, setup_ui):
        screen.fill((20, 20, 20))
        
        
        # ---------- Content generation toggle ----------
        label = self.font_small.render("Content Generation", True, (200, 200, 200))
        screen.blit(label, (20, 0))

        setup_ui.content_gen_buttons.draw(screen, self.font_small)

        label = self.font_small.render("Captions", True, (200, 200, 200))
        screen.blit(label, (20, 60))

        setup_ui.caption_buttons.draw(screen, self.font_small)

        # ---------- Title ----------
        title = self.font_large.render("Player Setup", True, (220, 220, 220))
        screen.blit(title, (self.screen_w // 2 - title.get_width() // 2, 60))

        # ---------- Labels ----------
        def draw_label(text, y):
            surf = self.font_small.render(text, True, (200, 200, 200))
            screen.blit(surf, (setup_ui.name_input.rect.x, y))

        draw_label("Name (optional)", setup_ui.name_label_y)
        draw_label("Age Group *",     setup_ui.age_label_y)
        draw_label("Mood *",          setup_ui.mood_label_y)
        draw_label("Likes",           setup_ui.likes_label_y)

        # ---------- Widgets ----------
        setup_ui.name_input.draw(screen, self.font_small)
        setup_ui.age_group_buttons.draw(screen, self.font_small)
        setup_ui.mood_buttons.draw(screen, self.font_small)
        setup_ui.likes_input.draw(screen, self.font_small)

        # ---------- Start ----------
        self._draw_start_button(
            screen,
            setup_ui.start_rect,
            enabled=setup_ui.is_valid(),
        )

        # ---------- Scoreboard button ----------
        self.scoreboard_button.draw(screen, self.font_small)
        
        # ---------- Hint ----------
        hint = self.font_small.render(
            "Click a field to type. Select an age group and mood.",
            True,
            (160, 160, 160),
        )
        screen.blit(
            hint,
            (self.screen_w // 2 - hint.get_width() // 2, self.screen_h - 40),
        )

    
    def _label(self, screen, text, y):
        surf = self.font_small.render(text, True, (200, 200, 200))
        screen.blit(surf, (self.screen_w // 2 - 140, y))

    def _draw_start_button(self, screen, rect, enabled: bool):
        if enabled:
            fill = (100, 200, 100)
            txtc = (20, 20, 20)
        else:
            fill = (70, 70, 70)
            txtc = (140, 140, 140)

        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), rect, 2, border_radius=8)

        txt = self.font_small.render("Start Game", True, txtc)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))


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
    # Lives
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

        # restart button is drawn by your existing logic elsewhere (same rect as before)
        # (main.py handles click)

    # =========================================================
    # Debug panel (UNCHANGED)
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
            
    def handle_event(self, event, game_manager):
        if game_manager.state == GameState.GAME_OVER:
            self.game_over_buttons.handle_event(event)

        if game_manager.state == GameState.PLAYER_SETUP:
            self.scoreboard_button.handle_event(event)

            
    def draw_game_over_preview(self, screen, scoreboard, current_entry):
        entries, idx = scoreboard.get_preview_for_entry(current_entry)

        x = self.screen_w // 2
        y = self.screen_h // 2 + 110
        line_h = 22

        title = self.font_small.render("Your Position", True, (220, 220, 220))
        screen.blit(title, (x - title.get_width() // 2, y))

        for i, e in enumerate(entries):
            mins = int(e["time"] // 60)
            secs = int(e["time"] % 60)
            prefix = ">> " if e == current_entry else "   "

            txt = self.font_small.render(
                f"{prefix}{e['name']}  {mins:02d}:{secs:02d}  K:{e['kills']}",
                True,
                (240, 240, 120) if e == current_entry else (200, 200, 200),
            )

            screen.blit(
                txt,
                (x - txt.get_width() // 2, y + 25 + i * line_h),
            )
    
    def draw_commentary(self, screen, text):
        if not text:
            return

        surf = self.font_small.render(text, True, (220, 220, 220))
        bg = pygame.Surface((surf.get_width() + 20, surf.get_height() + 12), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))

        x = self.screen_w // 2 - bg.get_width() // 2
        y = self.screen_h - 80

        screen.blit(bg, (x, y))
        screen.blit(surf, (x + 10, y + 6))


    # =========================================================
    # LOADING (DRAW ONLY)
    # =========================================================
    def draw_loading(self, screen, progress):
        completed, total, message = progress.snapshot()

        screen.fill((15, 15, 15))

        if total > 0:
            ratio = completed / total
        else:
            ratio = 0

        # ---- Title text ("Generating") ----
        title = self.font_large.render(
            "Generating",
            True,
            (200, 200, 200),
        )
        title_rect = title.get_rect(center=(400, 200))
        screen.blit(title, title_rect)

        # ---- Progress bar ----
        pygame.draw.rect(screen, (40, 40, 40), (200, 300, 400, 25))
        pygame.draw.rect(
            screen,
            (100, 200, 100),
            (200, 300, int(400 * ratio), 25),
        )

        # ---- Status text ----
        text = self.font_large.render(
            f"{message} ({completed}/{total})",
            True,
            (255, 255, 255),
        )
        text_rect = text.get_rect(center=(400, 260))
        screen.blit(text, text_rect)
