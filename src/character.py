import math
import pygame
from pygame.math import Vector2
from typing import Iterable, List, Tuple, Any, Union


class Shield:
    """A simple circular shield in world coordinates."""
    def __init__(self, world_center: Union[Tuple[float, float], Vector2],
                 radius: float, color=(50, 50, 200, 230), outline_alpha=200):
        self.world_center = Vector2(world_center)
        self.radius = float(radius)
        self.color = color
        self.outline_alpha = outline_alpha

    def set_center(self, world_center: Union[Tuple[float, float], Vector2]):
        self.world_center = Vector2(world_center)

    def collides_with(self, enemy: Any) -> bool:
        # obtain enemy position
        if hasattr(enemy, "pos"):
            epos = Vector2(enemy.pos)
        else:
            epos = Vector2(enemy)

        # estimate enemy radius if provided
        enemy_radius = 0.0
        for attr in ("radius", "r", "size"):
            if hasattr(enemy, attr):
                try:
                    val = float(getattr(enemy, attr))
                    if attr == "size":
                        enemy_radius = val / 2.0
                    else:
                        enemy_radius = val
                except Exception:
                    enemy_radius = 0.0
                break

        return ((epos - self.world_center).length()
                <= (self.radius + enemy_radius))

    def draw(self, overlay: pygame.Surface, to_screen):
        p = Vector2(to_screen(self.world_center))
        pygame.draw.circle(overlay, self.color,
                           (int(p.x), int(p.y)), max(1, int(self.radius)))
        # outline
        outline_color = (self.color[0], self.color[1],
                         self.color[2], self.outline_alpha)
        pygame.draw.circle(overlay, outline_color,
                           (int(p.x), int(p.y)), max(1, int(self.radius)), 2)


class Character:
    """
    Player centered on screen. Uses Shield objects for orbiting kill circles.
    If shield_segments == 0 there are no Shields (no legacy full-circle).
    """
    def __init__(
        self,
        screen_size: Tuple[int, int],
        pos: Tuple[float, float] = (0.0, 0.0),
        speed: float = 240.0,
        shield_radius: float = 120.0,
        player_radius: int = 12,
        player_color: Tuple[int, int, int] = (50, 200, 50),
        circle_color: Tuple[int, int, int] = (0, 0, 200),
        shield_segments: int = 0,
        shield_orbit_speed: float = 90.0,
        shield_orbit_ball_radius: float = 10.0,
    ):
        self.screen_size = Vector2(screen_size)
        self.screen_center = self.screen_size / 2
        self.pos = Vector2(pos)
        self.speed = speed
        self.shield_radius = float(shield_radius)
        self.player_radius = player_radius
        self.player_color = player_color
        self.circle_color = circle_color

        self.shield_segments = max(0, int(shield_segments))
        self.shield_orbit_speed = float(shield_orbit_speed)
        self.shield_orbit_ball_radius = float(shield_orbit_ball_radius)
        self._shield_phase = 0.0  # radians

        # shield instances (one per satellite). kept updated in update()
        self.shields: List[Shield] = []

        # player sprite
        size = max(2 * player_radius, 16)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(
            self.image,
            self.player_color,
            (size // 2, size // 2),
            player_radius,
        )
        self._image_offset = Vector2(self.image.get_size()) / 2

        # initialize zones if needed
        self._rebuild_Shields()

    def _rebuild_Shields(self):
        """
        Ensure Shields list has length == shield_segments.
        Centers updated each frame.
        """
        n = self.shield_segments
        if n <= 0:
            self.shields = []
            return
        if len(self.shields) != n:
            new = []
            for _ in range(n):
                kz = Shield(self.pos, self.shield_orbit_ball_radius,
                            color=(*self.circle_color, 230), outline_alpha=200)
                new.append(kz)
            self.shields = new
            self.shields = new

    def _update_Shield_positions(self):
        """Position each Shield on the orbit according to current phase."""
        n = self.shield_segments
        if n <= 0:
            return
        r = self.shield_radius
        for i, kz in enumerate(self.shields):
            angle = self._shield_phase + i * (math.tau / n)
            center = self.pos + Vector2(math.cos(angle), math.sin(angle)) * r
            kz.set_center(center)
            kz.radius = self.shield_orbit_ball_radius

    def handle_input(self, dt: float,
                     keys: pygame.key.ScancodeWrapper = None):
        if keys is None:
            keys = pygame.key.get_pressed()

        dir = Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dir.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dir.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dir.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dir.x += 1

        if dir.length_squared() > 0:
            dir = dir.normalize()
            self.pos += dir * self.speed * dt

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper = None):
        self.handle_input(dt, keys)
        # update phase
        if self.shield_segments > 0 and self.shield_orbit_speed != 0:
            self._shield_phase += math.radians(self.shield_orbit_speed) * dt
            if self._shield_phase > math.tau:
                self._shield_phase -= math.tau
        # rebuild zones if count changed and update positions
        self._rebuild_Shields()
        self._update_Shield_positions()

    def draw(self, surface: pygame.Surface):
        overlay = pygame.Surface((int(self.screen_size.x),
                                  int(self.screen_size.y)), pygame.SRCALPHA)
        overlay = pygame.Surface((int(self.screen_size.x),
                                  int(self.screen_size.y)), pygame.SRCALPHA)

        # draw Shields (no legacy full-circle when shield_segments == 0)
        for kz in self.shields:
            kz.draw(overlay, self.world_to_screen)

        surface.blit(overlay, (0, 0))

        # player sprite centered
        blit_pos = self.screen_center - self._image_offset
        surface.blit(self.image, blit_pos)

    def world_to_screen(self, world_pos: Union[Tuple[float, float],
                                               Vector2]) -> Vector2:
        wp = Vector2(world_pos)
        return wp - self.pos + self.screen_center

    def screen_to_world(self, screen_pos: Union[Tuple[float, float],
                                                Vector2]) -> Vector2:
        sp = Vector2(screen_pos)
        return sp - self.screen_center + self.pos

    def collides_with_enemy(self, enemy: Any) -> bool:
        # If there are no Shields, nothing collides (no legacy full-circle)
        if not self.shields:
            return False
        for kz in self.shields:
            if kz.collides_with(enemy):
                return True
        return False

    def kill_enemies(self, enemies: Iterable[Any]) -> List[Any]:
        killed = []
        for e in enemies:
            if self.collides_with_enemy(e):
                killed.append(e)
        return killed
