"""
sprites.py - 8-bit pixel art, drawn from text grids.

Each letter is a color from settings.PALETTE and "." is transparent.
Every art grid is 12x12 "pixels"; each pixel is drawn as a 4x4 block,
so a sprite fills one 48x48 maze tile.

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""
import pygame

from settings import (PALETTE, PLASTER, SHOJI_PAPER, SHOJI_WOOD, SPRITE_PIXEL,
                      TATAMI, TATAMI_EDGE, TATAMI_WEAVE, WOOD_DARK, WOOD_LIGHT,
                      WOOD_MID)

NINJA_ART = [
    "....KKKK....",
    "...KKKKKK...",
    "..KKKKKKKK..",
    "..RRRRRRRRRR",   # red headband (the tail flaps out the back)
    "..KSSSSSSK.R",
    "..KSKSSKSK..",   # eyes peeking out of the mask
    "..KKKKKKKK..",
    "...KKKKKK...",
    ".NKKKKKKKKN.",
    "S.KKRRRRKK.S",   # red belt
    "..KKK..KKK..",
    ".KKK....KKK.",
]

MONK_ART = [
    "....SSSS..Y.",   # shaved head; gold ring on top of the staff
    "...SSSSSS.YD",
    "...SKSSKS..D",   # calm eyes
    "...SSSSSS..D",
    "....SSSS...D",
    "..OOOOOOOO.D",   # saffron robe
    ".OOOKOOOOOSD",   # prayer beads + hand gripping the staff
    ".OOOOKOOOO.D",
    ".SBOOOKOOO.D",
    "..BOOOOOOO.D",
    "..BBOOOOOO.D",
    "..DD....DD..",   # sandals
]

SCROLL_ART = [
    "............",
    "............",
    ".RR......RR.",
    ".RPPPPPPPPR.",
    ".RPDPDDPDPR.",   # secret writing
    ".RPPPPPPPPR.",
    ".RPDDPDPDPR.",
    ".RPPPPPPPPR.",
    ".RR......RR.",
    "............",
    "............",
    "............",
]


def build_sprite(art, pixel=SPRITE_PIXEL):
    """Turn a text grid into a pygame Surface with transparency."""
    surf = pygame.Surface((len(art[0]) * pixel, len(art) * pixel), pygame.SRCALPHA)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.fill(PALETTE[ch], (x * pixel, y * pixel, pixel, pixel))
    return surf


def build_shoji_tile(size, px=SPRITE_PIXEL):
    """Inner walls: a shoji screen (paper panes in a wooden lattice)."""
    surf = pygame.Surface((size, size))
    surf.fill(SHOJI_PAPER)
    # thick frame around the edge
    pygame.draw.rect(surf, SHOJI_WOOD, (0, 0, size, size), px)
    # lattice: 2 columns x 3 rows of panes
    for x in (size // 2 - px // 2,):
        surf.fill(SHOJI_WOOD, (x, 0, px // 2 + 1, size))
    for y in (size // 3, 2 * size // 3):
        surf.fill(SHOJI_WOOD, (0, y, size, px // 2 + 1))
    # thick bottom rail like a real sliding door
    surf.fill(SHOJI_WOOD, (0, size - px * 2, size, px * 2))
    return surf


def build_temple_wall_tile(size, px=SPRITE_PIXEL):
    """Outer walls: white plaster panels framed by red lacquered beams and pillars."""
    surf = pygame.Surface((size, size))
    surf.fill(PLASTER)
    surf.fill(WOOD_MID, (0, 0, size, px * 2))                 # top beam
    surf.fill(WOOD_MID, (0, size - px * 2, size, px * 2))     # bottom beam
    surf.fill(WOOD_MID, (0, 0, px * 2, size))                 # pillar
    surf.fill(WOOD_LIGHT, (px // 2, 0, px // 2, size))        # lacquer shine
    surf.fill(WOOD_DARK, (0, px * 2, size, px // 2))          # beam shadow
    return surf


def build_tatami_tile(size, horizontal, px=SPRITE_PIXEL):
    """Floor: a tatami mat with woven straw and a dark green cloth edge.
    `horizontal` alternates the weave direction so the floor looks like real mats."""
    surf = pygame.Surface((size, size))
    surf.fill(TATAMI)
    for i in range(px, size, px * 2):
        if horizontal:
            surf.fill(TATAMI_WEAVE, (0, i, size, px // 2))
        else:
            surf.fill(TATAMI_WEAVE, (i, 0, px // 2, size))
    # mat border on the top and left edges -> forms a grid across the floor
    surf.fill(TATAMI_EDGE, (0, 0, size, px // 2 + 1))
    surf.fill(TATAMI_EDGE, (0, 0, px // 2 + 1, size))
    return surf
