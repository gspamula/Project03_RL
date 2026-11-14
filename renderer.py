"""
renderer.py - draws the temple, the characters and the scoreboard (HUD).
Drawing is kept separate from the game logic so training in turbo mode
never has to wait on graphics.

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""
import pygame

from settings import (GOLD, GREEN, GREY, HUD_BG, HUD_HEIGHT, RED, TILE, WHITE, WOOD_LIGHT)
from sprites import (NINJA_ART, MONK_ART, SCROLL_ART,
                     build_shoji_tile, build_sprite, build_tatami_tile,
                     build_temple_wall_tile)


class Renderer:
    """Draws everything on screen. Kept separate from the game logic, so the
    environment can run without graphics (turbo, headless, experiments)."""

    def __init__(self, screen, maze):
        """Build the sprites and pre-draw the static background once."""
        self.screen = screen
        self.maze = maze
        self.maze_h = maze.height * TILE
        self.width = maze.width * TILE
        # A small font with anti-aliasing OFF, scaled up 2x, looks blocky/8-bit.
        self.font = pygame.font.Font(None, 15)

        ninja = build_sprite(NINJA_ART)
        monk = build_sprite(MONK_ART)
        self.ninja_img = {1: ninja, -1: pygame.transform.flip(ninja, True, False)}
        self.monk_img = {1: monk, -1: pygame.transform.flip(monk, True, False)}
        self.scroll_img = build_sprite(SCROLL_ART)
        self.background = self._build_background()

    def _build_background(self):
        """Draw the temple once: red temple outer walls, shoji screens inside,
        tatami mats on the floor."""
        surf = pygame.Surface((self.width, self.maze_h))
        outer, shoji = build_temple_wall_tile(TILE), build_shoji_tile(TILE)
        tatami = {True: build_tatami_tile(TILE, True),
                  False: build_tatami_tile(TILE, False)}
        w, h = self.maze.width, self.maze.height
        for y in range(h):
            for x in range(w):
                if self.maze.is_wall((x, y)):
                    on_border = x in (0, w - 1) or y in (0, h - 1)
                    tile = outer if on_border else shoji
                else:
                    tile = tatami[(x + y) % 2 == 0]
                surf.blit(tile, (x * TILE, y * TILE))
        return surf

    def text(self, msg, x, y, color=WHITE, scale=2, center=False):
        """Draw blocky 8-bit text: render a small font without smoothing, then scale it up."""
        img = self.font.render(msg, False, color)
        img = pygame.transform.scale(img, (img.get_width() * scale,
                                           img.get_height() * scale))
        rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
        self.screen.blit(img, rect)

    # ------------------------------------------------------------------- draw
    def draw(self, env, title, lines, history, banner=None):
        """Draw one frame: background, scroll, ninja, monk, optional banner, and the HUD."""
        self.screen.blit(self.background, (0, 0))      # pre-drawn walls + tatami

        # Grid squares -> screen pixels: multiply by TILE (48).
        sx, sy = env.scroll_pos
        if env.ninja_pos != env.scroll_pos:            # hide it once grabbed
            self.screen.blit(self.scroll_img, (sx * TILE, sy * TILE))
        nx, ny = env.ninja_pos
        # facing picks the normal or mirrored sprite (left / right)
        self.screen.blit(self.ninja_img[env.ninja_facing], (nx * TILE, ny * TILE))
        kx, ky = env.monk_pos
        self.screen.blit(self.monk_img[env.monk_facing], (kx * TILE, ky * TILE))

        if banner:                     # end-of-game message, e.g. "CAUGHT!"
            msg, color = banner
            box = pygame.Rect(0, 0, 360, 70)
            box.center = (self.width // 2, self.maze_h // 2)
            pygame.draw.rect(self.screen, HUD_BG, box)
            pygame.draw.rect(self.screen, color, box, 4)
            self.text(msg, box.centerx, box.centery, color, scale=4, center=True)

        self._draw_hud(title, lines, history)
        pygame.display.flip()                          # show the finished frame

    def _draw_hud(self, title, lines, history):
        """Draw the scoreboard panel: title, stat lines and the win-rate graph."""
        top = self.maze_h                              # the HUD sits under the maze
        pygame.draw.rect(self.screen, HUD_BG, (0, top, self.width, HUD_HEIGHT))
        pygame.draw.rect(self.screen, WOOD_LIGHT, (0, top, self.width, HUD_HEIGHT), 4)  # wood frame
        self.text(title, 12, top + 8, GOLD)
        for i, (msg, color) in enumerate(lines):       # one stat per row, 22 px apart
            self.text(msg, 12, top + 34 + i * 22, color)
        self._draw_graph(history, pygame.Rect(440, top + 12, 268, HUD_HEIGHT - 24))

    def _draw_graph(self, history, area):
        """Bar chart of the ninja's win rate, one bar per block of episodes."""
        pygame.draw.rect(self.screen, GREY, area, 2)
        self.text("WIN RATE", area.x + 6, area.y + 4, GREY)
        if not history:
            self.text("training...", area.x + 6, area.y + 30, GREY)
            return
        shown = history[-40:]
        inner = area.inflate(-12, -34)
        inner.y = area.y + 28
        bar_w = max(2, inner.w // len(shown))
        for i, rate in enumerate(shown):
            h = int(rate * inner.h)
            color = GREEN if rate >= 0.7 else GOLD if rate >= 0.4 else RED
            self.screen.fill(color, (inner.x + i * bar_w, inner.bottom - h,
                                     bar_w - 2, h))
