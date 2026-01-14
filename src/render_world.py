import pygame
from typing import List
from character import Character
from enemy import Enemy


class WorldRenderer:
    def draw(self, screen: pygame.Surface,
             player: Character,
             enemies: List[Enemy]):
        # background
        screen.fill((30, 30, 40))

        # enemies
        for e in enemies:
            e.draw(screen, player.world_to_screen)

        # player (includes shields)
        player.draw(screen)
