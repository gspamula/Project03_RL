"""
tests.py - unit tests for the game rules and the Q-learning math.

Run with:   python -m unittest tests -v

These check that the environment hands out the right rewards and that the
agent's update matches the Q-learning formula, so when the ninja learns
something strange we know the bug is in the design, not the code.

AI assistance: written with help from Claude (Anthropic) - see README "AI use".
"""
import random
import unittest

from agent import QLearningAgent
from env import STAY, TempleEnv
from maze import Maze
from settings import (MAX_STEPS, MAZE_LAYOUT, REWARD_CAUGHT, REWARD_SCROLL,
                      REWARD_STEP, REWARD_WALL, SENSE_RANGE)

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3


class MazeTests(unittest.TestCase):
    """Checks that the map loads correctly and the monk's chase logic works."""

    def setUp(self):
        self.maze = Maze(MAZE_LAYOUT)

    def test_layout_is_parsed(self):
        self.assertEqual(self.maze.ninja_start, (1, 1))
        self.assertEqual(self.maze.monk_start, (7, 6))
        self.assertEqual(len(self.maze.scroll_spots), 4)

    def test_every_scroll_spot_is_reachable(self):
        for spot in self.maze.scroll_spots:
            self.assertIn(spot, self.maze.dist[self.maze.ninja_start])

    def test_action_toward_gets_closer(self):
        start, goal = self.maze.monk_start, self.maze.ninja_start
        action = self.maze.action_toward(start, goal)
        dx, dy = [(0, -1), (0, 1), (-1, 0), (1, 0)][action]
        nxt = (start[0] + dx, start[1] + dy)
        self.assertEqual(self.maze.dist[goal][nxt], self.maze.dist[goal][start] - 1)


class EnvTests(unittest.TestCase):
    """Checks the game rules: movement, walls, winning, being caught, timeouts and the state."""

    def setUp(self):
        self.env = TempleEnv(Maze(MAZE_LAYOUT), rng=random.Random(0))
        self.env.reset()

    def place_scroll(self, index):
        """Put the scroll in a chosen hiding spot (instead of a random one)."""
        self.env.scroll_index = index
        self.env.scroll_pos = self.env.maze.scroll_spots[index]

    def test_wall_bump_costs_extra_and_blocks(self):
        start = self.env.ninja_pos                     # (1,1): wall above
        _, reward, done, _ = self.env.step(UP, monk_action=STAY)
        self.assertEqual(self.env.ninja_pos, start)
        self.assertEqual(reward, REWARD_STEP + REWARD_WALL)
        self.assertFalse(done)

    def test_grabbing_scroll_wins(self):
        self.place_scroll(0)                          # scroll at (12,1)
        self.env.ninja_pos = (11, 1)
        _, reward, done, info = self.env.step(RIGHT, monk_action=STAY)
        self.assertTrue(done)
        self.assertEqual(info["result"], "scroll")
        self.assertEqual(reward, REWARD_STEP + REWARD_SCROLL)

    def test_same_square_is_caught(self):
        self.env.ninja_pos, self.env.monk_pos = (3, 3), (5, 3)
        _, reward, done, info = self.env.step(RIGHT, monk_action=LEFT)  # both land on (4,3)
        self.assertEqual(info["result"], "caught")
        self.assertEqual(reward, REWARD_STEP + REWARD_CAUGHT)

    def test_walking_through_each_other_is_caught(self):
        self.env.ninja_pos, self.env.monk_pos = (3, 3), (4, 3)
        _, _, done, info = self.env.step(RIGHT, monk_action=LEFT)       # swap squares
        self.assertTrue(done)
        self.assertEqual(info["result"], "caught")

    def test_timeout_is_truncated_not_terminal(self):
        self.env.steps = MAX_STEPS - 1
        self.env.ninja_pos, self.env.monk_pos = (3, 3), (13, 9)
        _, _, done, info = self.env.step(LEFT, monk_action=STAY)
        self.assertTrue(done)
        self.assertEqual(info["result"], "timeout")
        self.assertTrue(info["truncated"])

    def test_state_clips_monk_distance(self):
        self.place_scroll(2)
        self.env.ninja_pos, self.env.monk_pos = (1, 1), (13, 9)
        state = self.env.ninja_state()
        self.assertEqual(state, (1, 1, SENSE_RANGE, SENSE_RANGE, 2))

    def test_custom_rewards_and_blind_ninja(self):
        env = TempleEnv(Maze(MAZE_LAYOUT), rng=random.Random(0),
                        rewards={"wall": 0}, sense_range=0, see_scroll=False)
        _, reward, _, _ = env.step(UP, monk_action=STAY)
        self.assertEqual(reward, REWARD_STEP)          # no wall penalty
        self.assertEqual(env.ninja_state()[2:], (0, 0, 0))


class AgentTests(unittest.TestCase):
    """Checks the Q-learning math and the epsilon-greedy policy."""

    def test_q_update_matches_formula(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, rng=random.Random(0))
        agent.q["s2"] = [0.0, 10.0, 0.0, 0.0]
        agent.learn("s1", 2, reward=-1, next_state="s2", terminal=False)
        # 0 + 0.5 * (-1 + 0.9 * 10 - 0) = 4.0
        self.assertAlmostEqual(agent.q["s1"][2], 4.0)

    def test_terminal_update_ignores_future(self):
        agent = QLearningAgent(alpha=0.5, gamma=0.9, rng=random.Random(0))
        agent.q["s2"] = [50.0] * 4
        agent.learn("s1", 0, reward=100, next_state="s2", terminal=True)
        self.assertAlmostEqual(agent.q["s1"][0], 50.0)   # 0.5 * 100

    def test_greedy_picks_best_action(self):
        agent = QLearningAgent(rng=random.Random(0))
        agent.q["s"] = [1.0, 5.0, 2.0, -3.0]
        self.assertEqual(agent.choose_action("s", greedy=True), 1)

    def test_epsilon_decays_to_floor(self):
        agent = QLearningAgent(epsilon=1.0, epsilon_min=0.05, epsilon_decay=0.5)
        for _ in range(20):
            agent.decay_epsilon()
        self.assertEqual(agent.epsilon, 0.05)


if __name__ == "__main__":
    unittest.main()
