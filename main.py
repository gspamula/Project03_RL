"""
Temple Dash - an 8-bit reinforcement learning game.

A ninja must sneak through a temple and steal the secret scroll while a monk
hunts it down. The ninja starts knowing NOTHING about the rules (not even that
walls exist) and learns purely from rewards using Q-learning.

Modes:
    python main.py                 train with graphics (SPACE = turbo)
    python main.py --mode watch    watch the trained ninja (no learning)
    python main.py --mode play     YOU are the monk (arrow keys / WASD)
    python main.py --mode headless --episodes 5000   fast training, no window

Options:
    --rival learn    the monk is a second Q-learning agent instead of scripted
    --fresh          ignore saved Q-tables and start from scratch
    --skill 0.8      monk skill for watch/play mode

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""
import argparse
import csv
import os
import random
from collections import deque

import pygame

from agent import QLearningAgent
from env import STAY, TempleEnv
from maze import Maze
from renderer import Renderer
from settings import (AUTOSAVE_EVERY, BANNER_FRAMES, CURRICULUM_WINDOW, GOLD,
                      GREEN, GREY, HISTORY_BLOCK, HUD_HEIGHT, LEVEL_UP_WIN_RATE,
                      LOG_EVERY, HISTORY_KEEP, LOG_FILE, MAZE_LAYOUT, NINJA_QTABLE, PLAY_FPS, RED,
                      MONK_MAX_SKILL, MONK_QTABLE, MONK_START_SKILL,
                      SKILL_STEP, TILE, TURBO_STEPS_PER_FRAME, WATCH_FPS, WHITE)

HERE = os.path.dirname(os.path.abspath(__file__))

BANNERS = {
    "scroll": ("SCROLL GET!", GREEN),
    "caught": ("CAUGHT!", RED),
    "timeout": ("TIME UP", GREY),
}

# Keys for the human monk -> action numbers (0 up, 1 down, 2 left, 3 right)
KEY_ACTIONS = {pygame.K_UP: 0, pygame.K_w: 0, pygame.K_DOWN: 1, pygame.K_s: 1,
               pygame.K_LEFT: 2, pygame.K_a: 2, pygame.K_RIGHT: 3, pygame.K_d: 3}


class TempleDash:
    """The whole game: sets up the maze, environment and agents, runs the
    agent-environment loop, and handles stats, the curriculum, saving and drawing."""

    def __init__(self, args):
        """Build everything for the chosen mode and load a saved brain if there is one."""
        self.args = args
        self.mode = args.mode
        self.rng = random.Random(args.seed)
        self.maze = Maze(MAZE_LAYOUT)
        self.env = TempleEnv(self.maze, rng=self.rng)

        self.ninja = QLearningAgent(rng=self.rng)
        self.rival_learns = args.rival == "learn"
        self.monk = QLearningAgent(rng=self.rng) if self.rival_learns else None

        # What each mode does: train/headless learn and explore,
        # watch just shows off, play keeps learning a little against you.
        self.learn = self.mode in ("train", "headless", "play")
        self.greedy = self.mode == "watch"

        # Stats
        self.episode = 0
        self.wins = 0
        self.recent = deque(maxlen=CURRICULUM_WINDOW)   # 1 = win, 0 = not
        self.history = []        # win rate per HISTORY_BLOCK episodes (for the graph)
        self.block = []
        self.log_block = []      # (result, steps) for the next CSV summary row
        self.score_you = self.score_ninja = 0

        if not args.fresh:
            self.load()
        if self.mode in ("watch", "play"):
            if args.skill is not None:
                self.env.monk_skill = args.skill
            if self.mode == "play":
                self.ninja.epsilon = 0.05   # mostly use what it learned

        self.state = self.env.reset()
        self.log_file = self.log_writer = None
        if self.learn and self.mode != "play":
            path = os.path.join(HERE, LOG_FILE)
            new = not os.path.exists(path) or args.fresh
            self.log_file = open(path, "w" if args.fresh else "a", newline="")
            self.log_writer = csv.writer(self.log_file)
            if new:
                self.log_writer.writerow(["episode", "win_rate", "caught_rate",
                                          "timeout_rate", "avg_steps",
                                          "epsilon", "monk_skill"])

    # --------------------------------------------------------------- saving
    def load(self):
        """Load the saved ninja (and monk) Q-tables and the training stats."""
        path = os.path.join(HERE, NINJA_QTABLE)
        if os.path.exists(path):
            meta = self.ninja.load(path)
            # A brain trained with a different state (e.g. before the scroll
            # started moving) can't be reused, so start over instead.
            if self.ninja.q and len(next(iter(self.ninja.q))) != len(self.env.ninja_state()):
                print("Saved ninja brain is from an older version of the game - "
                      "starting fresh.")
                self.ninja.q, self.ninja.epsilon = {}, self.ninja.epsilon_start
                return
            self.episode = meta.get("episode", 0)
            self.wins = meta.get("wins", 0)
            self.history = meta.get("history", [])
            self.env.monk_skill = meta.get("skill", MONK_START_SKILL)
            print(f"Loaded ninja brain: {len(self.ninja.q)} states, "
                  f"episode {self.episode}")
        elif self.mode == "watch":
            print("No trained ninja found yet - run training first!")
        spath = os.path.join(HERE, MONK_QTABLE)
        if self.monk and os.path.exists(spath):
            self.monk.load(spath)

    def save(self):
        """Save the Q-table(s) and stats so training can continue later."""
        meta = {"episode": self.episode, "wins": self.wins,
                "history": self.history[-HISTORY_KEEP:], "skill": self.env.monk_skill}
        self.ninja.save(os.path.join(HERE, NINJA_QTABLE), meta)
        if self.monk:
            self.monk.save(os.path.join(HERE, MONK_QTABLE))
        if self.log_file:
            self.log_file.flush()

    # ------------------------------------------------------------ game loop
    def tick(self, human_action=None):
        """One turn of the agent-environment loop. Returns the result if the episode ended."""
        state = self.state
        action = self.ninja.choose_action(state, greedy=self.greedy)

        monk_action, s_state = None, None
        if self.mode == "play":
            monk_action = human_action
        elif self.monk:
            s_state = self.env.monk_state()
            monk_action = self.monk.choose_action(s_state, greedy=self.greedy)

        next_state, reward, done, info = self.env.step(action, monk_action)

        if self.learn:
            # Only real endings are terminal; a timeout still has future value.
            terminal = done and not info["truncated"]
            self.ninja.learn(state, action, reward, next_state, terminal)
            if s_state is not None:
                self.monk.learn(s_state, monk_action, info["monk_reward"],
                                info["monk_state"], terminal)
        self.state = next_state
        if done:
            self.end_episode(info["result"])
            return info["result"]
        return None

    def end_episode(self, result):
        """Bookkeeping after each game: stats, epsilon decay, CSV log,
        the monk's curriculum level-up and auto-saving."""
        self.episode += 1
        win = result == "scroll"
        self.wins += win
        self.recent.append(win)
        self.block.append(win)
        if len(self.block) == HISTORY_BLOCK:
            self.history.append(sum(self.block) / HISTORY_BLOCK)
            self.block = []

        if self.mode == "play":
            if win:
                self.score_ninja += 1
            elif result == "caught":
                self.score_you += 1

        if self.learn:
            self.ninja.decay_epsilon()
            if self.monk:
                self.monk.decay_epsilon()

        if self.log_writer:
            self.log_block.append((result, self.env.steps))
            if len(self.log_block) == LOG_EVERY:
                n = len(self.log_block)
                count = lambda r: sum(1 for res, _ in self.log_block if res == r) / n
                self.log_writer.writerow([
                    self.episode, round(count("scroll"), 3), round(count("caught"), 3),
                    round(count("timeout"), 3),
                    round(sum(s for _, s in self.log_block) / n, 1),
                    round(self.ninja.epsilon, 4), round(self.env.monk_skill, 2)])
                self.log_block = []

        # Curriculum: once the ninja beats this monk often enough,
        # the monk gets smarter. This keeps the challenge growing.
        if (self.learn and self.mode != "play" and not self.rival_learns
                and len(self.recent) == CURRICULUM_WINDOW
                and self.win_rate() >= LEVEL_UP_WIN_RATE
                and self.env.monk_skill < MONK_MAX_SKILL - 1e-9):
            self.env.monk_skill = round(self.env.monk_skill + SKILL_STEP, 2)
            self.recent.clear()
            print(f"Episode {self.episode}: monk levels up! "
                  f"skill = {self.env.monk_skill:.0%}")

        if self.learn and self.mode != "play" and self.episode % AUTOSAVE_EVERY == 0:
            self.save()

    def reset_episode(self):
        """Start a new game (new random scroll spot)."""
        self.state = self.env.reset()

    def win_rate(self):
        """Fraction of the last CURRICULUM_WINDOW games the ninja won."""
        return sum(self.recent) / len(self.recent) if self.recent else 0.0

    # ----------------------------------------------------------------- HUD
    def hud(self, turbo):
        """Title and text lines for the scoreboard under the maze."""
        if self.mode == "play":
            title = "TEMPLE DASH - YOU ARE THE MONK"
            lines = [(f"YOU {self.score_you}   NINJA {self.score_ninja}", WHITE),
                     ("ARROWS / WASD TO MOVE", GREY),
                     ("CATCH THE NINJA BEFORE", GREY),
                     ("IT GETS THE SCROLL!   ESC QUIT", GREY)]
            return title, lines
        label = {"train": "TURBO TRAINING" if turbo else "TRAINING",
                 "watch": "TURBO WATCH" if turbo else "WATCH MODE"}[self.mode]
        rival = ("MONK: LEARNING TOO" if self.rival_learns
                 else f"MONK SKILL {self.env.monk_skill:.0%}")
        lines = [(f"EPISODE {self.episode}   WINS {self.wins}", WHITE),
                 (f"WIN RATE {self.win_rate():.0%} (LAST {len(self.recent)})", WHITE),
                 (f"EXPLORING {self.ninja.epsilon:.0%}   {rival}", WHITE),
                 ("SPACE TURBO  S SAVE  ESC QUIT" if self.mode == "train"
                  else "SPACE TURBO  ESC QUIT", GREY)]
        return f"TEMPLE DASH - {label}", lines

    # ----------------------------------------------------------------- run
    def run_headless(self):
        """Train with no window as fast as possible, printing progress every 500 games."""
        for _ in range(self.args.episodes):
            while self.tick() is None:
                pass
            self.reset_episode()
            if self.episode % 500 == 0:
                print(f"episode {self.episode:6d}  win rate {self.win_rate():5.0%}  "
                      f"epsilon {self.ninja.epsilon:.3f}  "
                      f"skill {self.env.monk_skill:.0%}  states {len(self.ninja.q)}")
        self.save()

    def run(self):
        """Open the window and run the game loop: handle keys, step the game
        (one move per frame, or thousands in turbo), and draw."""
        if self.mode == "headless":
            return self.run_headless()

        pygame.init()
        screen = pygame.display.set_mode((self.maze.width * TILE,
                                          self.maze.height * TILE + HUD_HEIGHT))
        pygame.display.set_caption("Temple Dash - RL Ninja")
        renderer = Renderer(screen, self.maze)
        clock = pygame.time.Clock()
        turbo, banner, banner_left = False, None, 0
        queued = None          # last key tapped by the human between turns
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and self.mode in ("train", "watch"):
                        turbo = not turbo
                    elif event.key == pygame.K_s and self.mode == "train":
                        self.save()
                        print("Saved.")
                    elif event.key in KEY_ACTIONS:
                        queued = KEY_ACTIONS[event.key]

            if banner_left > 0:
                # Freeze on the final frame so you can see what happened.
                banner_left -= 1
                if banner_left == 0:
                    banner = None
                    self.reset_episode()
            elif turbo:
                for _ in range(TURBO_STEPS_PER_FRAME):
                    if self.tick() is not None:
                        self.reset_episode()
            else:
                human = None
                if self.mode == "play":
                    pressed = pygame.key.get_pressed()
                    held = [a for k, a in KEY_ACTIONS.items() if pressed[k]]
                    human = held[0] if held else (queued if queued is not None else STAY)
                    queued = None
                result = self.tick(human)
                if result:
                    banner, banner_left = BANNERS[result], BANNER_FRAMES

            title, lines = self.hud(turbo)
            renderer.draw(self.env, title, lines, self.history, banner)
            clock.tick(60 if turbo else PLAY_FPS if self.mode == "play" else WATCH_FPS)

        if self.learn:
            self.save()
        if self.log_file:
            self.log_file.close()
        pygame.quit()


def parse_args():
    """Read the command-line options (--mode, --rival, --fresh, ...)."""
    p = argparse.ArgumentParser(description="Temple Dash - RL ninja vs monk")
    p.add_argument("--mode", choices=["train", "watch", "play", "headless"],
                   default="train")
    p.add_argument("--rival", choices=["scripted", "learn"], default="scripted")
    p.add_argument("--episodes", type=int, default=5000, help="headless mode only")
    p.add_argument("--skill", type=float, default=None,
                   help="monk skill 0-1 for watch/play mode")
    p.add_argument("--fresh", action="store_true", help="start from scratch")
    p.add_argument("--seed", type=int, default=None)
    return p.parse_args()


if __name__ == "__main__":
    TempleDash(parse_args()).run()
