import pygame
from ui.select_buttons import SelectButtons


class ScoreboardRenderer:
    def __init__(self, screen_size):
        self.screen_w, self.screen_h = screen_size

        self.font_small = pygame.font.SysFont(None, 22)
        self.font_large = pygame.font.SysFont(None, 48)

        # default sort
        self.sort_key = "time"
        self.sort_reverse = True  # higher time first

        # ---------- sort buttons ----------
        self.sort_buttons = SelectButtons([
            ("Time",  (self.screen_w // 2 - 220, 80, 120, 36)),
            ("Kills", (self.screen_w // 2 -  60, 80, 120, 36)),
            ("Name",  (self.screen_w // 2 + 100, 80, 120, 36)),
        ])

        # ---------- back button ----------
        self.back_button = SelectButtons([
            ("Back", (20, self.screen_h - 60, 120, 40)),
        ])

        self.back_requested = False

    # =========================================================
    # Input
    # =========================================================

    def handle_event(self, event):
        self.back_requested = False

        self.sort_buttons.handle_event(event)
        self.back_button.handle_event(event)

        # ----- sort handling -----
        if self.sort_buttons.selected:
            label = self.sort_buttons.selected
            self.sort_buttons.selected = None

            if label == "Time":
                self.sort_key = "time"
                self.sort_reverse = True
            elif label == "Kills":
                self.sort_key = "kills"
                self.sort_reverse = True
            elif label == "Name":
                self.sort_key = "name"
                self.sort_reverse = False

        # ----- back handling -----
        if self.back_button.selected:
            self.back_button.selected = None
            self.back_requested = True

    # =========================================================
    # Draw
    # =========================================================

    def draw(self, screen, entries):
        screen.fill((15, 15, 15))

        # ---------- title ----------
        title = self.font_large.render("Scoreboard", True, (220, 220, 220))
        screen.blit(
            title,
            (self.screen_w // 2 - title.get_width() // 2, 20),
        )

        # ---------- buttons ----------
        self.sort_buttons.draw(screen, self.font_small)
        self.back_button.draw(screen, self.font_small)

        # ---------- headers ----------
        headers = ["#", "Name", "Age Group", "Mood", "Time", "Kills"]
        col_x   = [80, 120, 280, 380, 480, 580]
        y = 140

        for text, x in zip(headers, col_x):
            surf = self.font_small.render(text, True, (180, 180, 180))
            screen.blit(surf, (x, y))

        # ---------- sort ----------
        entries = sorted(
            entries,
            key=lambda e: e.get(self.sort_key, 0),
            reverse=self.sort_reverse,
        )

        # ---------- rows ----------
        row_y = y + 30
        for i, e in enumerate(entries[:15]):  # top 15
            mins = int(e.get("time", 0) // 60)
            secs = int(e.get("time", 0) % 60)
            time_str = f"{mins:02d}:{secs:02d}"

            values = [
                str(i + 1),
                e.get("name") or "Anonymous",
                e.get("age_group", "-"),
                e.get("mood", "-"),
                time_str,
                str(e.get("kills", 0)),
            ]

            for val, x in zip(values, col_x):
                surf = self.font_small.render(val, True, (220, 220, 220))
                screen.blit(surf, (x, row_y))

            row_y += 24
