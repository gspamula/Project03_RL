# Presentation guide: Temple Dash

Aim for about 8–10 minutes plus questions. Before class, back up the trained brain:

```bash
cp ninja_qtable.pkl ninja_qtable_trained.pkl
```

---

## 1. The idea (1 min)
- "A ninja has to steal a scroll from a temple while a monk chases it. The ninja starts knowing **nothing**: not where the walls are, not that the monk is dangerous."
- Why this game: a small maze means a Q-table can hold every situation, so you can actually see *what* it learned.

## 2. Live demo: it starts dumb (2 min)
```bash
python main.py --fresh
```
- Let it run at normal speed for ~10 seconds: the ninja wanders randomly and bumps into walls. Point at **EXPLORING 100%**.
- Press **SPACE** (turbo). Point at the win-rate bars climbing and the "monk levels up" messages in the terminal.
- Press SPACE again around MONK SKILL 100% and watch it dodge.
- If anything goes wrong, restore the backup with `cp ninja_qtable_trained.pkl ninja_qtable.pkl`, then run `python main.py --mode watch`.

## 3. How it learns (3 min). Show the code.
1. **Loop:** `main.py` → `tick()`: state → action → `env.step()` → reward → `learn()`.
2. **State** (`env.py` → `ninja_state`): its position, where the monk is (up to 3 squares), which spot the scroll is in.
3. **Rewards** (`settings.py`): −1 per move, −5 wall, +100 scroll, −100 caught.
4. **Q-learning** (`agent.py` → `learn`): one line of math. Explain the target: "the reward I got, plus the best I think I can do from where I landed."
5. **ε-greedy** (`agent.py` → `choose_action`): explore at first, exploit later.

## 4. Evidence: experiments (2 min)
Show `results/learning_curves.png` and the table in the README.
- "Without seeing the monk it wins 17%. Without knowing the scroll spot, 50%. So every part of my state matters."
- "Removing the −1 per move dropped it to 85%: it stopped hurrying."
- "Surprise: the wall penalty didn't matter, because bumping a wall already wastes a turn."

## 5. Creative twists (1 min)
Curriculum (the monk gets smarter), moving scroll, both sides learning (`--rival learn`), original pixel art.

## 6. Challenge a classmate (1–2 min)
```bash
python main.py --mode play
```
A classmate controls the monk with the arrow keys and tries to catch the trained ninja.

## 7. AI use (30 s)
"I used Claude to help write the code. It's documented at the top of every file and in the README. I chose the design, trained it, and here's what I changed myself: …"

---

## Likely questions and good answers

**What's the state space?**
Five numbers: the ninja's x and y, the monk's offset dx and dy (clipped to ±3), and the scroll spot (0–3). That's about 14,900 possible states, of which about 6,100 actually come up.

**Why clip the monk distance to 3?**
The ninja doesn't need to tell "5 squares away" from "9 squares away"; both just mean "far". Clipping keeps the table small, so it learns faster.

**Why Q-learning and not a neural network?**
The state is small and made of whole numbers, so a table fits every state, learns in seconds, and I can print a Q-value to see why it made a move. A neural network would only add training time.

**What is γ (gamma)?**
How much future rewards count. 0.95 means a reward 20 moves away still matters (0.95²⁰ ≈ 0.36). With 0.5, a reward 20 moves away is worth almost nothing, and my experiment showed it does worse.

**What is α (alpha)?**
How far each new experience moves the old estimate. 0.05 was too slow in my experiments; 0.2 worked best.

**What does ε do, and why does it decay?**
It's the chance of a random move. At the start the ninja knows nothing, so exploring is the only way to find the scroll. Later, random moves just get it caught, so ε shrinks to 5%.

**Why is the training win rate ~78% but the test win rate 100%?**
During training it still makes 5% random moves, which sometimes walk it into the monk. In the test, exploration is off.

**What happens on a timeout?**
The game is cut short, but the position wasn't actually bad, so the update still adds the future value γ·max Q(s'). Only grabbing the scroll or being caught counts as a real end.

**How does the monk work?**
With probability equal to its skill, it takes a step along the shortest path to the ninja, computed with BFS in `maze.py`. Otherwise it moves randomly. The skill rises 10% each time the ninja wins 70% of its last 100 games.

**How do you know your code is correct?**
`tests.py` has 14 unit tests. They check the rewards for walls, the scroll, being caught and timeouts, and they check the Q-update against the formula worked out by hand.

**What would you do next?**
Random maze layouts, so the ninja has to generalize: then a position-based table wouldn't be enough, and I'd need features or a neural network. Or making the monk learn your habits in play mode.
