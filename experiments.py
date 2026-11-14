"""
experiments.py - tuning experiments: does each design choice actually help?

Trains the ninja from scratch under several different designs (rewards,
what it can see, hyperparameters), several times each, then tests every
trained ninja with exploration OFF. Writes:

    results/experiments.md       table of results (pasted into the README)
    results/experiments.csv      same numbers as CSV
    results/learning_curves.png  win rate while training, one line per design

Run with:   python experiments.py            (takes about a minute)
            python experiments.py --quick    (fewer episodes, for a fast check)

To keep the comparison fair, every run uses the same fixed monk
(skill 1.0 = always chases, no curriculum) and the same random seeds.

AI assistance: written with help from Claude (Anthropic) - see README "AI use".
"""
import argparse
import csv
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # draw the chart without a window
import pygame

from agent import QLearningAgent
from env import TempleEnv
from maze import Maze
from settings import MAZE_LAYOUT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
MONK_SKILL = 1.0
BLOCK = 100          # learning curve resolution (episodes per point)

# name, environment options, agent options, why we tried it
VARIANTS = [
    ("Baseline", {}, {},
     "the design used in the game"),
    ("No wall penalty", {"rewards": {"wall": 0}}, {},
     "is the -5 for bumping walls needed?"),
    ("No step penalty", {"rewards": {"step": 0}}, {},
     "does -1 per move make it hurry?"),
    ("Can't see the monk", {"sense_range": 0}, {},
     "how much does seeing the monk matter?"),
    ("Sees monk 1 square", {"sense_range": 1}, {},
     "smaller state - learns faster or worse?"),
    ("Can't see scroll spot", {"see_scroll": False}, {},
     "must it know where the scroll is?"),
    ("gamma = 0.5", {}, {"gamma": 0.5},
     "only cares about the near future"),
    ("alpha = 0.05", {}, {"alpha": 0.05},
     "learns in smaller steps"),
]


def run_episode(env, agent, learn, greedy):
    """Play one game. Returns the result ('scroll', 'caught' or 'timeout')."""
    state = env.reset()
    while True:
        action = agent.choose_action(state, greedy=greedy)
        next_state, reward, done, info = env.step(action)
        if learn:
            agent.learn(state, action, reward, next_state,
                        done and not info["truncated"])
        state = next_state
        if done:
            if learn:
                agent.decay_epsilon()
            return info["result"]


def run_variant(env_opts, agent_opts, episodes, seed, eval_games):
    """Train one ninja with the given design, then test it with exploration off.
    Returns (learning curve, test results, episodes to reach 70%, states learned)."""
    rng = random.Random(seed)
    env = TempleEnv(Maze(MAZE_LAYOUT), monk_skill=MONK_SKILL, rng=rng, **env_opts)
    agent = QLearningAgent(rng=rng, **agent_opts)

    curve, wins = [], 0
    for ep in range(1, episodes + 1):
        wins += run_episode(env, agent, learn=True, greedy=False) == "scroll"
        if ep % BLOCK == 0:
            curve.append(wins / BLOCK)
            wins = 0

    # Test: exploration off, no more learning.
    results = [run_episode(env, agent, learn=False, greedy=True)
               for _ in range(eval_games)]
    test = {r: results.count(r) / eval_games for r in ("scroll", "caught", "timeout")}
    first_70 = next((i * BLOCK + BLOCK for i, w in enumerate(curve) if w >= 0.7), None)
    return curve, test, first_70, len(agent.q)


def draw_chart(curves, path, episodes):
    """Draw every design's learning curve on one chart and save it as a PNG."""
    pygame.init()
    W, H, L, R, T, B = 1000, 560, 70, 290, 50, 60
    surf = pygame.Surface((W, H))
    surf.fill((255, 255, 255))
    font = pygame.font.Font(None, 22)
    big = pygame.font.Font(None, 30)
    plot = pygame.Rect(L, T, W - L - R, H - T - B)
    colors = [(30, 30, 30), (220, 50, 50), (240, 150, 30), (40, 120, 220),
              (120, 190, 240), (150, 70, 180), (40, 160, 90), (150, 150, 150)]

    surf.blit(big.render(f"Ninja win rate while training (monk skill {MONK_SKILL:.0%}, "
                         "average of 3 seeds)", True, (0, 0, 0)), (L, 14))
    for pct in (0, 25, 50, 75, 100):
        y = plot.bottom - pct / 100 * plot.h
        pygame.draw.line(surf, (225, 225, 225), (plot.x, y), (plot.right, y))
        surf.blit(font.render(f"{pct}%", True, (90, 90, 90)), (L - 45, y - 8))
    for k in range(0, episodes + 1, episodes // 6):
        x = plot.x + k / episodes * plot.w
        surf.blit(font.render(f"{k:,}", True, (90, 90, 90)), (x - 15, plot.bottom + 8))
    surf.blit(font.render("episodes", True, (90, 90, 90)), (plot.centerx - 30, plot.bottom + 32))
    pygame.draw.rect(surf, (120, 120, 120), plot, 1)

    for i, (name, curve) in enumerate(curves):
        color = colors[i % len(colors)]
        pts = [(plot.x + (j + 1) * BLOCK / episodes * plot.w,
                plot.bottom - w * plot.h) for j, w in enumerate(curve)]
        if len(pts) > 1:
            pygame.draw.lines(surf, color, False, pts, 4 if i == 0 else 2)
        ly = T + 10 + i * 28
        pygame.draw.line(surf, color, (W - R + 20, ly + 8), (W - R + 50, ly + 8), 4)
        surf.blit(font.render(name, True, (0, 0, 0)), (W - R + 58, ly))
    pygame.image.save(surf, path)


def main():
    """Run every design in VARIANTS and write the results/ files."""
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    args = p.parse_args()
    episodes, seeds, eval_games = (1500, [1], 200) if args.quick else (6000, [1, 2, 3], 1000)
    os.makedirs(OUT, exist_ok=True)

    rows, curves = [], []
    for name, env_opts, agent_opts, why in VARIANTS:
        runs = [run_variant(env_opts, agent_opts, episodes, s, eval_games) for s in seeds]
        avg = lambda vals: sum(vals) / len(vals)
        curve = [avg(c) for c in zip(*(r[0] for r in runs))]
        test_win = avg([r[1]["scroll"] for r in runs])
        test_caught = avg([r[1]["caught"] for r in runs])
        test_timeout = avg([r[1]["timeout"] for r in runs])
        reached = [r[2] for r in runs]
        to70 = (f"{avg(reached):,.0f}" if all(reached) else
                f"{avg([x for x in reached if x]):,.0f} ({reached.count(None)} never)"
                if any(reached) else "never")
        states = avg([r[3] for r in runs])
        rows.append([name, why, test_win, test_caught, test_timeout, to70, states])
        curves.append((name, curve))
        print(f"{name:24s} test win {test_win:6.1%}  caught {test_caught:6.1%}  "
              f"timeout {test_timeout:6.1%}  reached 70% at {to70:>12s}  states {states:,.0f}")

    with open(os.path.join(OUT, "experiments.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant", "question", "test_win_rate", "test_caught_rate",
                    "test_timeout_rate", "episodes_to_70pct", "states_learned"])
        for r in rows:
            w.writerow([r[0], r[1], f"{r[2]:.3f}", f"{r[3]:.3f}", f"{r[4]:.3f}", r[5], f"{r[6]:.0f}"])

    with open(os.path.join(OUT, "experiments.md"), "w") as f:
        f.write(f"Trained {episodes:,} episodes x {len(seeds)} seeds per design vs. a "
                f"{MONK_SKILL:.0%}-skill monk, then tested in {eval_games:,} games with "
                "exploration off.\n\n")
        f.write("| Design | Question | Test win | Caught | Timeout | Episodes to 70% | States |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r[0]} | {r[1]} | **{r[2]:.0%}** | {r[3]:.0%} | {r[4]:.0%} | "
                    f"{r[5]} | {r[6]:,.0f} |\n")

    draw_chart(curves, os.path.join(OUT, "learning_curves.png"), episodes)
    print("Saved results/experiments.md, results/experiments.csv, results/learning_curves.png")


if __name__ == "__main__":
    main()
