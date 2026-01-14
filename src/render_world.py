import random
import pygame
from pygame.math import Vector2

from world_objects import WorldObjectManager, CHUNK_SIZE
from asset_loader import load_images_from_folder


class WorldRenderer:
    def __init__(self):
        # --------------------------------------------------
        # Load background tiles (biomes)
        # --------------------------------------------------
        self.bg_tiles = load_images_from_folder(
            "assets/backgrounds",
            alpha=False,
        )

        self.tile_size = self.bg_tiles[0].get_width()

        # --------------------------------------------------
        # Load props
        # --------------------------------------------------
        prop_images = load_images_from_folder(
            "assets/props",
            alpha=True,
        )

        self.world_objects = WorldObjectManager(prop_images)

    # ==================================================
    # Public
    # ==================================================

    def draw(self, screen, player, enemies):
        self._draw_background(screen, player)
        self.world_objects.update(player.pos)
        self._draw_world_objects(screen, player)
        self._draw_enemies(screen, player, enemies)
        self._draw_player(screen, player)

    # ==================================================
    # Background (chunk-based biome tiling)
    # ==================================================

    def _draw_background(self, screen, player):
        w, h = screen.get_size()

        top_left = player.screen_to_world((0, 0))
        bottom_right = player.screen_to_world((w, h))

        start_cx = int(top_left.x // CHUNK_SIZE)
        end_cx = int(bottom_right.x // CHUNK_SIZE) + 1
        start_cy = int(top_left.y // CHUNK_SIZE)
        end_cy = int(bottom_right.y // CHUNK_SIZE) + 1

        for cx in range(start_cx, end_cx):
            for cy in range(start_cy, end_cy):
                tile = self._get_tile_for_chunk(cx, cy)
                self._draw_chunk(screen, player, cx, cy, tile)

    def _get_tile_for_chunk(self, cx, cy):
        seed = cx * 73856093 ^ cy * 19349663
        random.seed(seed)
        return random.choice(self.bg_tiles)


    def _draw_chunk(self, screen, player, cx, cy, tile):
        origin = Vector2(cx * CHUNK_SIZE, cy * CHUNK_SIZE)
        tiles_per_chunk = CHUNK_SIZE // self.tile_size + 1

        for tx in range(tiles_per_chunk):
            for ty in range(tiles_per_chunk):
                world_pos = origin + Vector2(
                    tx * self.tile_size,
                    ty * self.tile_size,
                )
                screen_pos = player.world_to_screen(world_pos)
                screen.blit(tile, screen_pos)

    # ==================================================
    # World objects & entities
    # ==================================================

    def _draw_world_objects(self, screen, player):
        for obj in self.world_objects.objects:
            obj.draw(screen, player.world_to_screen)

    def _draw_enemies(self, screen, player, enemies):
        for e in enemies:
            e.draw(screen, player.world_to_screen)

    def _draw_player(self, screen, player):
        player.draw(screen)
