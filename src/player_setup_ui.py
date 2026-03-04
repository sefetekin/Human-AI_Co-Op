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
        y = 110   # top anchor for the form

        
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
        # ---------- Background Object ----------
        self.background_label_y = y
        y += GAP

        btn_w = (COLUMN_W - 20) // 3
        btn_h = FIELD_H

        self.background_buttons = SelectButtons([
            ("Mountain",       (LEFT_X,               y, btn_w, btn_h)),
            ("Toy Dinosaurs",  (LEFT_X + btn_w + 10,  y, btn_w, btn_h)),
            ("Houses",         (LEFT_X + 2*(btn_w+10),y, btn_w, btn_h)),
        ])

        y += FIELD_H + GAP

        self.background_input = TextInput(
            (LEFT_X, y, COLUMN_W, FIELD_H),
            numeric=False,
            max_len=48,
            placeholder="Desert, Forest, Rock",
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

        # --- always active fields ---
        self.name_input.handle_event(event)
        self.likes_input.handle_event(event)
        self.age_group_buttons.handle_event(event)
        self.mood_buttons.handle_event(event)
        self.content_gen_buttons.handle_event(event)
        self.caption_buttons.handle_event(event)

        # --- determine generation state ---
        gen_on = self.content_gen_buttons.selected == "Gen ON"

        # enable / disable controls
        self.background_buttons.enabled = gen_on
        self.background_input.enabled = gen_on

        # reset when turning off
        if not gen_on:
            self.background_buttons.selected = None
            self.background_input.text = ""

        # --- now process events for background ---
        self.background_buttons.handle_event(event)
        self.background_input.handle_event(event)

        # --- start button ---
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
        self.background_buttons.selected = None
        self.background_input.text = ""
        self.background_input.active = False

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
            "background": self.get_background_objects(),
        }
    
    def get_background_objects(self):
        # textbox overrides button
        bg_text = self.background_input.text.strip()

        if bg_text:
            background_objects = [x.strip() for x in bg_text.split(",") if x.strip()]
        elif self.background_buttons.selected:
            background_objects = [self.background_buttons.selected]
        else:
            background_objects = []
        return background_objects
    
    def content_gen_enabled(self):
        return self.content_gen_buttons.selected == "Gen ON"
