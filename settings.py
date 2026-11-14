"""
settings.py - every tunable number for Temple Dash lives here.

Keeping the rewards and hyperparameters in one file makes it easy to run
experiments ("what if the wall penalty is bigger?") without hunting
through the code.

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""

# ---------------------------------------------------------------------------
# Screen / drawing
# ---------------------------------------------------------------------------
TILE = 48                 # size of one maze square in screen pixels
SPRITE_PIXEL = 4          # one "8-bit pixel" = 4x4 screen pixels (12x12 art -> 48x48)
HUD_HEIGHT = 150          # scoreboard area under the maze
WATCH_FPS = 10            # moves per second when you watch normally
PLAY_FPS = 6              # moves per second in human-vs-ninja mode
TURBO_STEPS_PER_FRAME = 3000  # training steps per frame in turbo mode
BANNER_FRAMES = 6         # how long "CAUGHT!" / "SCROLL GET!" stays up

# ---------------------------------------------------------------------------
# The temple maze
#   #  wall      .  floor
#   N  ninja start   S  monk start
#   $  a hiding spot for the scroll (one is picked at random each round)
# ---------------------------------------------------------------------------
MAZE_LAYOUT = [
    "###############",
    "#N....#.....$.#",
    "#.##.##.###.#.#",
    "#.#.........#.#",
    "#.#.###.###.#.#",
    "#.....#.#$....#",
    "###.#.#S#.#.###",
    "#...#.....#...#",
    "#.#####.#####.#",
    "#$...........$#",
    "###############",
]

MAX_STEPS = 150           # an episode ends in a timeout after this many moves

# ---------------------------------------------------------------------------
# Rewards - the ninja is NEVER told the rules of the game.
# These numbers are the only feedback it gets.
# ---------------------------------------------------------------------------
REWARD_STEP = -1          # every move costs a little, so it learns to hurry
REWARD_WALL = -5          # walking into a wall wastes a turn
REWARD_SCROLL = 100       # grabbing the scroll = win
REWARD_CAUGHT = -100      # being caught by the monk = loss

# ---------------------------------------------------------------------------
# Q-learning hyperparameters
# ---------------------------------------------------------------------------
ALPHA = 0.2               # learning rate: how far each new experience moves a Q-value
GAMMA = 0.95              # discount: how much future rewards matter vs. right now
EPSILON_START = 1.0       # start fully random (pure exploration)
EPSILON_MIN = 0.05        # always keep a little exploration
EPSILON_DECAY = 0.998     # multiply epsilon by this after every episode
SENSE_RANGE = 3           # ninja "sees" the monk up to 3 squares away on each axis

# ---------------------------------------------------------------------------
# Monk curriculum: the monk gets smarter as the ninja gets better
# skill = chance that the monk moves straight toward the ninja
# (otherwise it wanders randomly)
# ---------------------------------------------------------------------------
MONK_START_SKILL = 0.3
MONK_MAX_SKILL = 1.0
SKILL_STEP = 0.1
LEVEL_UP_WIN_RATE = 0.7   # ninja must win 70% of the last window to level up the monk
CURRICULUM_WINDOW = 100   # episodes per check
HISTORY_BLOCK = 50        # the HUD graph shows one bar per 50 episodes

# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
NINJA_QTABLE = "ninja_qtable.pkl"
MONK_QTABLE = "monk_qtable.pkl"
LOG_FILE = "training_log.csv"
LOG_EVERY = 100           # one summary row per 100 episodes (keeps the CSV small)
HISTORY_KEEP = 1000       # how many graph bars to keep in the save file
AUTOSAVE_EVERY = 200      # episodes

# ---------------------------------------------------------------------------
# 8-bit palette (one letter per color, used by the pixel art in sprites.py)
# ---------------------------------------------------------------------------
PALETTE = {
    "K": (20, 20, 32),     # ninja black
    "N": (56, 56, 110),    # navy shadow
    "R": (216, 40, 40),    # red
    "S": (252, 188, 140),  # skin
    "Y": (248, 200, 40),   # gold
    "W": (230, 230, 240),  # steel / white
    "D": (90, 56, 30),     # dark brown
    "P": (240, 220, 160),  # paper
    "O": (236, 132, 36),   # saffron robe
    "B": (184, 92, 24),    # robe shadow
}

# Temple look: tatami mats, shoji paper screens, red-and-white outer walls
TATAMI = (200, 184, 112)        # woven straw
TATAMI_WEAVE = (176, 160, 92)
TATAMI_EDGE = (44, 72, 44)      # dark green cloth border on each mat
SHOJI_PAPER = (238, 230, 206)
SHOJI_WOOD = (110, 68, 36)
WOOD_DARK = (60, 20, 16)       # dark gaps / beam
WOOD_MID = (176, 46, 34)       # vermilion lacquer
WOOD_LIGHT = (214, 88, 60)     # lacquer shine
PLASTER = (240, 236, 226)      # white temple wall plaster

HUD_BG = (40, 24, 16)
WHITE = (240, 240, 240)
GOLD = (248, 200, 40)
RED = (230, 60, 60)
GREEN = (90, 210, 90)
GREY = (130, 130, 150)
