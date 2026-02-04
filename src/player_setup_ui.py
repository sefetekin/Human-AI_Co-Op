import pygame
from ui.text_input import TextInput
from ui.select_buttons import SelectButtons


class PlayerSetupUI:
    def __init__(self, screen_size):
        w, h = screen_size

        # ---------- Content generation toggle ----------
        self.content_gen_buttons = SelectButtons([
            ("Gen ON",  (20, 20, 90, 32)),
            ("Gen OFF", (115, 20, 90, 32)),
        ])

        # default selection
        self.content_gen_buttons.selected = "Gen OFF"
        
        # ---------- Caption toggle ----------
        self.caption_buttons = SelectButtons([
            ("Caption ON",  (20, 80, 90, 32)),
            ("Caption OFF", (115, 80, 90, 32)),
        ])

        # default selection
        self.caption_buttons.selected = "Caption OFF"

        # ---------- Layout constants ----------
        COLUMN_W = 360
        FIELD_H = 36
        GAP = 14
        SECTION_GAP = 28

        LEFT_X = (w - COLUMN_W) // 2
        y = 140   # top anchor for the form

        
        # ---------- Name ----------
        self.name_label_y = y
        y += GAP

        self.name_input = TextInput(
            (LEFT_X, y, COLUMN_W, FIELD_H),
            numeric=False,
            max_len=16,
            placeholder="Name (optional)",
        )
        y += FIELD_H + SECTION_GAP

        # ---------- Age Group ----------
        self.age_label_y = y
        y += GAP

        btn_w = (COLUMN_W - 20) // 3
        btn_h = FIELD_H

        self.age_group_buttons = SelectButtons([
            ("<18",   (LEFT_X,               y, btn_w, btn_h)),
            ("18–25", (LEFT_X + btn_w + 10,  y, btn_w, btn_h)),
            (">25",   (LEFT_X + 2*(btn_w+10),y, btn_w, btn_h)),
        ])
        y += FIELD_H + SECTION_GAP

        # ---------- Mood ----------
        self.mood_label_y = y
        y += GAP

        self.mood_buttons = SelectButtons([
            ("Chill",   (LEFT_X,               y, btn_w, btn_h)),
            ("Focused", (LEFT_X + btn_w + 10,  y, btn_w, btn_h)),
            ("Fun",     (LEFT_X + 2*(btn_w+10),y, btn_w, btn_h)),
        ])
        y += FIELD_H + SECTION_GAP

        # ---------- Likes ----------
        self.likes_label_y = y
        y += GAP

        self.likes_input = TextInput(
            (LEFT_X, y, COLUMN_W, FIELD_H),
            numeric=False,
            max_len=32,
            placeholder="Likes (e.g. music, games)",
        )
        y += FIELD_H + SECTION_GAP

        # ---------- Start ----------
        self.start_rect = pygame.Rect(
            LEFT_X,
            y,
            COLUMN_W,
            48,
        )

        self.start_requested = False

    # --------------------------------------------------

    def handle_event(self, event):
        self.start_requested = False

        self.name_input.handle_event(event)
        self.likes_input.handle_event(event)
        self.age_group_buttons.handle_event(event)
        self.mood_buttons.handle_event(event)
        self.content_gen_buttons.handle_event(event)
        self.caption_buttons.handle_event(event)


        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_valid() and self.start_rect.collidepoint(event.pos):
                self.start_requested = True

    def reset(self):
        self.name_input.text = ""
        self.name_input.active = False

        self.likes_input.text = ""
        self.likes_input.active = False

        self.age_group_buttons.selected = None
        self.mood_buttons.selected = None

        # ✅ RESET CONTENT GENERATION TO DEFAULT
        self.content_gen_buttons.selected = "Gen OFF"

        self.start_requested = False

    def is_valid(self):
        return (
            self.age_group_buttons.selected is not None
            and self.mood_buttons.selected is not None
        )

    def get_profile(self):
        return {
            "name": self.name_input.text.strip() or "Anonymous",
            "age_group": self.age_group_buttons.selected,
            "mood": self.mood_buttons.selected,
            "likes": self.likes_input.text.strip(),
            "content_generation": self.content_gen_buttons.selected,
            "captions": self.caption_buttons.selected,
        }
