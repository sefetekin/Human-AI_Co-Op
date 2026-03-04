import pygame


class SelectButtons:
    def __init__(self, buttons):
        """
        buttons: list of (label, rect)
        """
        self.buttons = [(label, pygame.Rect(rect)) for label, rect in buttons]
        self.selected = None
        self.enabled = True

    def handle_event(self, event: pygame.event.Event):
        if not self.enabled:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for label, rect in self.buttons:
                if rect.collidepoint(event.pos):
                    self.selected = label
                    return

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        for label, rect in self.buttons:
            is_sel = (label == self.selected)

            if not self.enabled:
                fill = (60,60,60)
                border = (120,120,120)
            else:
                fill = (100,200,100) if is_sel else (40,40,40)
                border = (20,20,20) if is_sel else (220,220,220)

            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, 2, border_radius=8)

            txt = font.render(label, True, (20, 20, 20) if is_sel else (220, 220, 220))
            screen.blit(
                txt,
                (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2),
            )
