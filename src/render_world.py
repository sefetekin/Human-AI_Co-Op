import random
import os
from collections import defaultdict

from pygame.math import Vector2
import math

from world_objects import WorldObjectManager, CHUNK_SIZE
from asset_loader import load_images_from_folder


# ==================================================
# Biome configuration
# ==================================================

BIOME_SIZE = 2  # number of chunks per biome region (2–4 recommended)


# ==================================================
# World Renderer
# ==================================================

class WorldRenderer:
    def __init__(self, content_generation: bool = True):
        # --------------------------------------------------
        # Load background tiles (grouped by terrain name)
        # --------------------------------------------------
        bg_folder = "outputs" if content_generation else "assets/backgrounds"

        self.terrain_tiles = defaultdict(list)

        images_with_paths = load_images_from_folder(
            bg_folder,
            alpha=False,
            return_paths=True,
        )

        for img, path in images_with_paths:
            filename = os.path.basename(path)
            terrain = filename.split("_")[0]  # grass_01.png → grass
            self.terrain_tiles[terrain].append(img)

        if not self.terrain_tiles:
            raise RuntimeError("No background tiles found!")

        self.terrain_names = list(self.terrain_tiles.keys())
        self.tile_size = next(iter(self.terrain_tiles.values()))[0].get_width()

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

    def draw(self, screen, player, enemies, dt):
        self._draw_background(screen, player)
        self.world_objects.update(player.pos)
        self._draw_world_objects(screen, player, dt)
        self._draw_enemies(screen, player, enemies)
        self._draw_player(screen, player)

    def get_terrain_at_world_pos(self, world_pos: Vector2) -> str:
        

        cx = math.floor(world_pos.x / CHUNK_SIZE)
        cy = math.floor(world_pos.y / CHUNK_SIZE)
        return self._get_terrain_for_chunk(cx, cy)

    # ==================================================
    # Background (biome-based chunk tiling)
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

    # --------------------------------------------------
    # Biome logic
    # --------------------------------------------------

    def _chunk_to_biome(self, cx, cy):
        return cx // BIOME_SIZE, cy // BIOME_SIZE

    def _get_terrain_for_chunk(self, cx, cy):
        bx, by = self._chunk_to_biome(cx, cy)

        seed = bx * 73856093 ^ by * 19349663
        rng = random.Random(seed)

        return rng.choice(self.terrain_names)

    def _get_tile_for_chunk(self, cx, cy):
        terrain = self._get_terrain_for_chunk(cx, cy)

        seed = cx * 73856093 ^ cy * 19349663 + 999
        rng = random.Random(seed)

        return rng.choice(self.terrain_tiles[terrain])

    # --------------------------------------------------
    # Drawing helpers
    # --------------------------------------------------

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

    def _draw_world_objects(self, screen, player, dt):
        for obj in self.world_objects.objects:
            obj.draw(screen, player.world_to_screen)

        for c in self.world_objects.collectibles:
            c.update(dt)
            c.draw(screen, player.world_to_screen)

    def _draw_enemies(self, screen, player, enemies):
        for e in enemies:
            e.draw(screen, player.world_to_screen)

    def _draw_player(self, screen, player):
        player.draw(screen)
