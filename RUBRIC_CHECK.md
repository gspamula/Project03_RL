# Rubric check: Temple Dash vs. Project 03 brief

Checked against `Proj03_RL_PygAIme.pdf` (the project brief and its rubric) on 2026-11-14.
✅ = met · 🔧 = fixed in this review · 🙋 = you need to do it (code can't)

---

## Project requirements (page 1 of the brief)

| Requirement | Status | Where / notes |
|---|---|---|
| Game made with Python + Pygame | ✅ | `main.py`, `renderer.py` |
| "Game starts without knowing its rules" | ✅ | Q-table starts empty, ε = 1.0. Rules live only in `env.py`. `--fresh` shows this live |
| Learning algorithm that improves over iterations | ✅ | Q-learning, `agent.py`. Win rate goes from ~0% to 100% (test) |
| Coded, **tested**, refined | 🔧 | Added `tests.py` (14 unit tests) and `experiments.py` (8 designs × 3 seeds) |
| Presented to classmates | 🙋 | See `PRESENTATION.md` |
| PyCharm project called **`Project03_RL`** | ✅ / 🙋 | The GitHub repo is named **`Project03_RL`**. The folder on your Mac is still `xx_PyGAIme`; that only matters if Mr. Cochran checks the PyCharm project name |
| Shared to GitHub; all files + companion data committed | ✅ | Pushed to the private repo https://github.com/gspamula/Project03_RL: all 25 files, including the trained brain, `results/` and `docs/`. A fresh clone passes all tests and the brain wins 500/500 games. 🔧 Fixed a blocker: `training_log.csv` was **1.58 GB** (GitHub's limit is 100 MB per file). The log now writes one row per 100 episodes; the old file is in your Trash |
| Add `juliancochran` as a collaborator | ✅ | Invite sent (write access). It shows as *pending* until he accepts |
| README with collaboration, how to run/test, extra info | 🔧 | README sections "Quick start" (run), "Testing" and "Resources, collaboration and AI use" |
| Submit repo HTTPS link in Veracross | 🙋 | Submit `https://github.com/gspamula/Project03_RL.git` (the green **Code** button → HTTPS) |
| Honor code: document AI use **in the code** and explain how it was used | 🔧 | "AI assistance" note added to the top of every `.py` file; the README's "AI use" part explains it in detail; the full chat is in `AI_CHAT_LOGS.md` (re-export it right before the final GitHub push so it's complete). 🙋 Finish the "What I did" part in your own words |
| Document online resources used | 🔧 / 🙋 | README "Resources" list added. Fill in the links you actually read |

---

## Rubric criteria

### 1. Concept Understanding (10 pts)
*Needs: agent–environment loop, state and action spaces, reward function, learning algorithm; "clearly articulates the problem the agent is solving and justifies the choice of RL approach."*

| Item | Status | Where |
|---|---|---|
| Agent–environment loop | ✅ | README "How the ninja learns" diagram, `env.py` docstring |
| State and action spaces | ✅ 🔧 | README "How the ninja learns", now with a table explaining *why* each part of the state is there |
| Reward function | ✅ 🔧 | README "How the ninja learns", now with evidence for each reward |
| Problem the agent solves | 🔧 | README intro and "The game" section |
| Justify the choice of RL approach | 🔧 | "Why a Q-table instead of a neural network?" in README "How the ninja learns" |
| **You can explain it out loud** | 🙋 | This is graded in your oral defense. See the Q&A in `PRESENTATION.md` |

### 2. Technical Implementation (10 pts)
*Needs: well-organized, efficient code; complete and correct RL pipeline (environment → state → reward → action selection → improvement).*

| Item | Status | Notes |
|---|---|---|
| Organized into classes / modules | ✅ | 6 classes, one job each; all settings in `settings.py` |
| Efficient | ✅ | Shortest paths pre-computed; turbo runs ~3,000 steps per frame; 6,000 episodes train in ~2 s |
| Complete pipeline | ✅ | reset → state → ε-greedy action → step → reward → Q update → ε decay |
| **Correctness: timeouts** | 🔧 | A timeout was treated as a real ending (no future value). Now it's marked `truncated`, and the update still uses γ·max Q(s'). This is the textbook-correct handling |
| Data files stay a sane size | 🔧 | Log: one row per 100 episodes. Save file: graph history capped (brain file went from 9 MB to 350 KB) |
| Old saves can't crash a new version | ✅ | Detects a brain from an older state format and starts fresh |

### 3. Algorithm Design (10 pts)
*Needs: well-defined state space, carefully constructed reward, justified action policy, "evidence of iteration and tuning."*

| Item | Status | Notes |
|---|---|---|
| State space well-defined and justified | ✅ 🔧 | Experiments prove each part matters (17% win without the monk position, 50% without the scroll spot) |
| Reward function constructed and tested | 🔧 | The experiments tested removing each penalty. Honest finding: the wall penalty is optional |
| Action policy justified | 🔧 | New ε-greedy section in README "How the ninja learns" (why explore, why decay, why keep 5%) |
| **Evidence of iteration and tuning** | 🔧 | Two empty "your experiment" rows before. Now: an 8-design × 3-seed experiment table, a learning-curve chart, and a 6-version development history (README "Results" and "How the design evolved") |

### 4. Presentation and Communication (10 pts)
*Needs: explain the RL process, agent design, rewards, results; "demonstrates the agent learning in real time"; answer questions.*

| Item | Status | Notes |
|---|---|---|
| Live learning demo | ✅ | `python main.py --fresh`, then SPACE for turbo: the win-rate graph climbs and the monk levels up |
| Training results to show | 🔧 | Before/after GIFs in `docs/`, `results/learning_curves.png` and the experiments table |
| Audience participation | ✅ | `--mode play`: a classmate plays the monk |
| Talk structure and Q&A prep | 🔧 | New `PRESENTATION.md` |
| Actually presenting | 🙋 | Practice once with a timer |

### 5. Innovation and Creativity (5 pts)
*Needs: "goes meaningfully beyond standard tutorials."*

✅ Curriculum learning (the monk levels up), a moving objective, both sides learning (arms race), human vs. AI mode, and fully original 8-bit art drawn in code. None of these are in the snake or brick-breaker tutorials linked in the brief.

### 6. Code Documentation (5 pts)
*Needs: project objective, algorithm design, code structure, training results; thorough inline comments; detailed README; key design choices explained.*

| Item | Status |
|---|---|
| Project objective | 🔧 README intro and "The game" section |
| RL algorithm design | ✅ README "How the ninja learns" |
| Code structure | ✅ README "Project structure" (includes tests, experiments, results, docs) |
| Training results | 🔧 README "Results": before/after GIFs, chart, table, conclusions |
| Inline comments | 🔧 Every file has a header docstring. 33 missing class/function docstrings were added, so every class and function now has one (checked automatically); more line comments were added in `renderer.py` |
| Design choices explained | 🔧 README "How the ninja learns" and "What I learned from them" |

### 7. Meeting Project and Submission Guidelines (5 pts)
*Needs: GitHub repo, regular commits, all code and data pushed, teacher added, link submitted.*

✅ Private GitHub repo (it satisfies both the brief's "can be public" and the rubric's "private"), 8 commits so far, all code and data pushed, teacher invited.
🙋 Still to do: submit the link in Veracross, and keep committing and pushing as you make changes, e.g. after filling in the README placeholders.

---

## Graded outside the code
| Item | Points | Status |
|---|---|---|
| Blog post (reflection) | 15 | 🙋 Good material: the experiments section, and what surprised you (the wall penalty didn't matter; a blind ninja hides until time runs out) |
| Peer assessments | 10 | 🙋 Score classmates fairly; outlier scores get flagged |
