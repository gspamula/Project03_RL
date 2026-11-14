"""
env.py - the reinforcement-learning ENVIRONMENT.

The agent-environment loop:
    state  --->  agent picks an action  --->  env.step(action)
      ^                                            |
      +------  new state + reward + done  <--------+

The environment knows the rules (walls, scroll, getting caught).
The ninja agent does not - it only ever sees states and rewards.

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""
import random

from maze import ACTIONS
from settings import (MAX_STEPS, REWARD_CAUGHT, REWARD_SCROLL, REWARD_STEP,
                      REWARD_WALL, MONK_START_SKILL, SENSE_RANGE)

STAY = 4   # extra action only the human-controlled monk can use


def clip(value, low, high):
    """Keep `value` between `low` and `high` (used to limit how far the ninja can see)."""
    return max(low, min(high, value))


class TempleEnv:
    """The game world: positions, rules, rewards. The agents only see what step() returns."""

    def __init__(self, maze, monk_skill=MONK_START_SKILL, rng=None,
                 rewards=None, sense_range=SENSE_RANGE, see_scroll=True):
        """
        rewards / sense_range / see_scroll let experiments.py try other
        designs (e.g. no wall penalty, a blind ninja) without editing settings.py.
        """
        self.maze = maze
        self.monk_skill = monk_skill
        self.rng = rng or random.Random()
        r = {"step": REWARD_STEP, "wall": REWARD_WALL,
             "scroll": REWARD_SCROLL, "caught": REWARD_CAUGHT}
        r.update(rewards or {})
        self.rewards = r
        self.sense_range = sense_range
        self.see_scroll = see_scroll
        self.reset()

    def reset(self):
        """Put everyone back at the start. Returns the ninja's first state."""
        self.ninja_pos = self.maze.ninja_start
        self.monk_pos = self.maze.monk_start
        # The scroll is hidden in a random spot each round.
        self.scroll_index = self.rng.randrange(len(self.maze.scroll_spots))
        self.scroll_pos = self.maze.scroll_spots[self.scroll_index]
        self.ninja_facing = 1       # 1 = right, -1 = left (only for drawing)
        self.monk_facing = -1
        self.steps = 0
        self.done = False
        return self.ninja_state()

    # ------------------------------------------------------------------ states
    def ninja_state(self):
        """
        What the ninja observes:
          (its x, its y, monk dx, monk dy, which hiding spot has the scroll)
        The monk offset is clipped to +/-SENSE_RANGE, so "far away in that
        direction" all looks the same. The scroll spot is just a number
        (0-3), so the ninja can learn a different route for each spot while
        the Q-table stays small (~100 squares x 7 x 7 offsets x 4 spots).
        """
        nx, ny = self.ninja_pos
        sx, sy = self.monk_pos
        r = self.sense_range
        spot = self.scroll_index if self.see_scroll else 0
        return (nx, ny, clip(sx - nx, -r, r), clip(sy - ny, -r, r), spot)

    def monk_state(self):
        """Same idea from the monk's point of view (used if the monk learns)."""
        nx, ny = self.ninja_pos
        sx, sy = self.monk_pos
        r = self.sense_range
        return (sx, sy, clip(nx - sx, -r, r), clip(ny - sy, -r, r),
                self.scroll_index)

    # ---------------------------------------------------------------- movement
    def _try_move(self, pos, action):
        """Returns (new_position, bumped_wall)."""
        if action == STAY:
            return pos, False
        dx, dy = ACTIONS[action]
        new = (pos[0] + dx, pos[1] + dy)
        if self.maze.is_wall(new):
            return pos, True
        return new, False

    def scripted_monk_action(self):
        """Built-in monk: chases with probability `skill`, otherwise wanders."""
        if self.rng.random() < self.monk_skill:
            return self.maze.action_toward(self.monk_pos, self.ninja_pos)
        return self.rng.choice(self.maze.valid_actions(self.monk_pos))

    # -------------------------------------------------------------------- step
    def step(self, ninja_action, monk_action=None):
        """
        Advance the game one turn.
        monk_action=None means "use the built-in scripted monk".
        Returns: (ninja_state, ninja_reward, done, info)
        info["truncated"] is True when the game ended only because time ran
        out - that is not a real ending, so the agent should still value the
        future (see QLearningAgent.learn).
        """
        rw = self.rewards
        self.steps += 1
        ninja_reward = rw["step"]
        monk_reward = rw["step"]
        old_ninja, old_monk = self.ninja_pos, self.monk_pos
        result = None

        # 1) Ninja moves first.
        self.ninja_pos, bumped = self._try_move(old_ninja, ninja_action)
        if bumped:
            ninja_reward += rw["wall"]
        if self.ninja_pos[0] != old_ninja[0]:
            self.ninja_facing = 1 if self.ninja_pos[0] > old_ninja[0] else -1

        if self.ninja_pos == self.scroll_pos:
            result = "scroll"          # grabbed it before the monk could react
        else:
            # 2) Monk moves.
            if monk_action is None:
                monk_action = self.scripted_monk_action()
            self.monk_pos, s_bumped = self._try_move(old_monk, monk_action)
            if s_bumped:
                monk_reward += rw["wall"]
            if self.monk_pos[0] != old_monk[0]:
                self.monk_facing = 1 if self.monk_pos[0] > old_monk[0] else -1

            # Caught = same square, or they walked through each other.
            swapped = (self.monk_pos == old_ninja and self.ninja_pos == old_monk)
            if self.monk_pos == self.ninja_pos or swapped:
                result = "caught"
            elif self.steps >= MAX_STEPS:
                result = "timeout"

        if result == "scroll":
            ninja_reward += rw["scroll"]
            monk_reward += rw["caught"]      # monk "loses"
        elif result == "caught":
            ninja_reward += rw["caught"]
            monk_reward += rw["scroll"]      # monk "wins"

        self.done = result is not None
        info = {"result": result,
                "truncated": result == "timeout",
                "monk_reward": monk_reward,
                "monk_state": self.monk_state()}
        return self.ninja_state(), ninja_reward, self.done, info
