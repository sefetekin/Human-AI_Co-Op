import pygame


class TextInput:
    def __init__(self, rect, *, numeric=False, max_len=16, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.numeric = numeric
        self.max_len = max_len
        self.placeholder = placeholder

        self.text = ""
        self.active = False
        self.enabled = True

    def handle_event(self, event: pygame.event.Event):
        if not self.enabled:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return

            if event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                return

            if len(self.text) >= self.max_len:
                return

            ch = event.unicode
            if not ch or not ch.isprintable():
                return

            if self.numeric and not ch.isdigit():
                return

            self.text += ch

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        if not self.enabled:
            border = (80,80,80)
        elif self.active:
            border = (255,255,255)
        else:
            border = (160,160,160)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=6)

        shown = self.text if self.text else self.placeholder
        color = (255, 255, 255) if self.text else (140, 140, 140)

        surf = font.render(shown, True, color)
        screen.blit(
            surf,
            (self.rect.x + 8, self.rect.y + self.rect.height // 2 - surf.get_height() // 2),
        )
