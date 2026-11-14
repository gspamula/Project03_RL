r"""
agent.py - a tabular Q-learning agent.

The Q-table maps   state -> [Q(up), Q(down), Q(left), Q(right)]
where Q(s, a) is the agent's estimate of "total future reward if I take
action a in state s and play well afterwards".

After every move it nudges the estimate toward what actually happened:

    Q(s,a) <- Q(s,a) + alpha * ( r + gamma * max_a' Q(s',a')  -  Q(s,a) )
                                 \_____________________/
                                   the "target": reward now
                                   + best value of where I landed

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""
import pickle
import random

from settings import ALPHA, EPSILON_DECAY, EPSILON_MIN, EPSILON_START, GAMMA


class QLearningAgent:
    """The ninja's brain: a table of Q-values plus the rules for using and updating it."""

    def __init__(self, n_actions=4, alpha=ALPHA, gamma=GAMMA,
                 epsilon=EPSILON_START, epsilon_min=EPSILON_MIN,
                 epsilon_decay=EPSILON_DECAY, rng=None):
        """Set the hyperparameters (see settings.py) and start with an empty Q-table."""
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_start = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.rng = rng or random.Random()
        self.q = {}   # state tuple -> list of Q-values (unseen states start at 0)

    def q_values(self, state):
        """Q-values for a state; a state seen for the first time starts at all zeros."""
        if state not in self.q:
            self.q[state] = [0.0] * self.n_actions
        return self.q[state]

    def choose_action(self, state, greedy=False):
        """
        Epsilon-greedy policy:
          with probability epsilon -> random action (explore)
          otherwise                -> best known action (exploit)
        Ties are broken randomly so a brand-new agent doesn't always go "up".
        """
        if not greedy and self.rng.random() < self.epsilon:
            return self.rng.randrange(self.n_actions)
        qs = self.q_values(state)
        best = max(qs)
        return self.rng.choice([a for a, q in enumerate(qs) if q == best])

    def learn(self, state, action, reward, next_state, terminal):
        """
        One Q-learning update (see the formula at the top of this file).
        terminal=True only for REAL endings (scroll grabbed / caught).
        A timeout is not terminal: the game was cut short, but the position
        still had future value, so we keep the gamma * max Q(s') part.
        """
        qs = self.q_values(state)
        if terminal:
            target = reward                     # nothing comes after the end
        else:
            target = reward + self.gamma * max(self.q_values(next_state))
        qs[action] += self.alpha * (target - qs[action])

    def decay_epsilon(self):
        """Explore a little less after each episode."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    # ------------------------------------------------------------ save / load
    def save(self, path, meta=None):
        """Write the Q-table, epsilon and extra stats (`meta`) to a file with pickle."""
        with open(path, "wb") as f:
            pickle.dump({"q": self.q, "epsilon": self.epsilon,
                         "meta": meta or {}}, f)

    def load(self, path):
        """Loads a Q-table we saved ourselves. Returns the extra `meta` dict."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.q = data["q"]
        self.epsilon = data["epsilon"]
        return data.get("meta", {})
