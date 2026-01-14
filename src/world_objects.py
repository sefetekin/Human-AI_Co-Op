import random
import pygame
from pygame.math import Vector2

CHUNK_SIZE = 800


def world_to_chunk(pos: Vector2):
    return (
        int(pos.x // CHUNK_SIZE),
        int(pos.y // CHUNK_SIZE),
    )


class WorldObject:
    def __init__(self, pos: Vector2, image: pygame.Surface):
        self.pos = Vector2(pos)
        self.image = image
        self.offset = Vector2(image.get_size()) / 2

    def draw(self, screen, to_screen):
        p = to_screen(self.pos)
        screen.blit(self.image, p - self.offset)


class WorldObjectManager:
    def __init__(self, prop_images):
        self.prop_images = prop_images
        self.generated_chunks = set()
        self.objects = []

    def update(self, player_pos: Vector2):
        cx, cy = world_to_chunk(player_pos)

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                chunk = (cx + dx, cy + dy)
                if chunk not in self.generated_chunks:
                    self._generate_chunk(chunk)

    def _generate_chunk(self, chunk):
        cx, cy = chunk

        seed = cx * 73856093 ^ cy * 19349663
        rng = random.Random(seed)

        count = rng.randint(3, 8)
        for _ in range(count):
            x = cx * CHUNK_SIZE + rng.randint(0, CHUNK_SIZE)
            y = cy * CHUNK_SIZE + rng.randint(0, CHUNK_SIZE)
            img = rng.choice(self.prop_images)
            self.objects.append(WorldObject((x, y), img))

        self.generated_chunks.add(chunk)

