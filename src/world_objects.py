import math
import random
import pygame
from pygame.math import Vector2
from enum import Enum, auto

class CollectibleType(Enum):
    HEART = auto()
    SHIELD = auto()
    BROKEN_SHIELD = auto()
    LIGHTNING = auto()
    TRAP = auto()


CHUNK_SIZE = 800


def world_to_chunk(pos: Vector2):
    return (
        int(pos.x // CHUNK_SIZE),
        int(pos.y // CHUNK_SIZE),
    )


class WorldObject:
    def __init__(self, pos: Vector2, image: pygame.Surface):
        self.pos = Vector2(pos)               # world-space center
        self.image = image
        self.offset = Vector2(image.get_size()) / 2

        w, h = self.image.get_size()
        self.world_rect = pygame.Rect(
            int(self.pos.x - w / 2),
            int(self.pos.y - h / 2),
            w, h
        )

    def draw(self, screen, to_screen):
        p = to_screen(self.pos)
        screen.blit(self.image, p - self.offset)


class Collectible:
    def __init__(self, pos: Vector2, image: pygame.Surface, ctype: CollectibleType):
        self.pos = Vector2(pos)
        self.image = image
        self.type = ctype
        self.time = random.random() * 2 * math.pi   # start phase random
        self.bob_speed = 1.8
        self.bob_height = 4

        self.offset = Vector2(image.get_size()) / 2
        w, h = self.image.get_size()

        self.radius = max(w, h) / 2

    def update(self, dt):
        self.time += dt * self.bob_speed

    def draw(self, screen, to_screen):
        p = to_screen(self.pos)

        bob_offset = math.sin(self.time) * self.bob_height

        screen.blit(
            self.image,
            (p.x - self.offset.x, p.y - self.offset.y + bob_offset)
        )

    def collides_with_player(self, player):
        return (player.pos - self.pos).length() <= (player.player_radius + self.radius)

class WorldObjectManager:
    def __init__(self, prop_images):
        self.prop_images = []
        self.collectibles = []
        self.collectible_images = {
            CollectibleType.HEART: pygame.image.load(
                "assets/collectibles/heart.png"
            ).convert_alpha(),

            CollectibleType.SHIELD: pygame.image.load(
                "assets/collectibles/shield.png"
            ).convert_alpha(),

            CollectibleType.BROKEN_SHIELD: pygame.image.load(
                "assets/collectibles/broken_shield.png"
            ).convert_alpha(),

            CollectibleType.LIGHTNING: pygame.image.load(
                "assets/collectibles/lightning.png"
            ).convert_alpha(),

            CollectibleType.TRAP: pygame.image.load(
                "assets/collectibles/trap.png"
            ).convert_alpha(),
        }
        for k in self.collectible_images:
            self.collectible_images[k] = pygame.transform.smoothscale(
                self.collectible_images[k],
                (24, 24)
            )

        for img in prop_images:
            w, h = img.get_size()
            scaled = pygame.transform.smoothscale(
                img,
                (w // 4, h // 4)
            )
            self.prop_images.append(scaled)

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
        
    
    def collides_circle(self, center: Vector2, radius: float) -> bool:
        # Circle vs AABB collision
        r2 = radius * radius

        for obj in self.objects:
            rect = obj.world_rect

            # closest point on rect to circle center
            cx = max(rect.left, min(center.x, rect.right))
            cy = max(rect.top,  min(center.y, rect.bottom))

            dx = center.x - cx
            dy = center.y - cy

            if dx*dx + dy*dy <= r2:
                return True

        return False

    def resolve_circle_penetration(self, pos: Vector2, radius: float) -> Vector2:

        corrected = Vector2(pos)

        for obj in self.objects:
            rect = obj.world_rect

            # find closest point on rect
            closest = Vector2(
                max(rect.left, min(corrected.x, rect.right)),
                max(rect.top,  min(corrected.y, rect.bottom))
            )

            offset = corrected - closest
            dist = offset.length()

            if dist < radius:
                # push out along smallest axis
                if dist == 0:
                    # fully inside → pick shortest exit
                    dx_left  = abs(corrected.x - rect.left)
                    dx_right = abs(rect.right - corrected.x)
                    dy_top   = abs(corrected.y - rect.top)
                    dy_bot   = abs(rect.bottom - corrected.y)

                    m = min(dx_left, dx_right, dy_top, dy_bot)

                    if m == dx_left:
                        corrected.x = rect.left - radius
                    elif m == dx_right:
                        corrected.x = rect.right + radius
                    elif m == dy_top:
                        corrected.y = rect.top - radius
                    else:
                        corrected.y = rect.bottom + radius

                else:
                    push = offset.normalize() * (radius - dist)
                    corrected += push

        return corrected
    def spawn_collectible(self, pos, difficulty_score=0.5):

        types = [
            CollectibleType.HEART,
            CollectibleType.SHIELD,
            CollectibleType.BROKEN_SHIELD,
            CollectibleType.LIGHTNING,
            CollectibleType.TRAP,
        ]

        pos_count = 3
        neg_count = 2
        # Positive: HEART, SHIELD, LIGHTNING
        # Negative: BROKEN_SHIELD, TRAP

        neg_weight = 0.5 + difficulty_score * 0.5   # → 0.5 → 1.0
        pos_weight = 1 - neg_weight              # keeps total balanced

        probabilities = [
            pos_weight * 1/pos_count,  # HEART
            pos_weight * 1/pos_count,  # SHIELD
            neg_weight * 1/neg_count,   # BROKEN_SHIELD
            pos_weight * 1/pos_count,  # LIGHTNING
            neg_weight * 1/neg_count,   # TRAP
        ]

        ctype = random.choices(types, probabilities)[0]

        image = self.collectible_images[ctype]

        self.collectibles.append(
            Collectible(pos, image, ctype)
        )