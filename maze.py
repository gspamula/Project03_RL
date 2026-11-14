"""
maze.py - the Maze class reads the ASCII layout and answers questions about it
(is this a wall? which way is the shortest path?).

AI assistance: written with help from Claude (Anthropic) via Claude Code;
reviewed, run and tuned by me. See README "AI use" for details.
"""
from collections import deque

# Index of each move. The order matters: the agents pick actions by number.
ACTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]   # up, down, left, right
ACTION_NAMES = ["UP", "DOWN", "LEFT", "RIGHT"]


class Maze:
    """The temple map: walls, floor squares, start positions and scroll hiding spots."""

    def __init__(self, layout):
        """Parse the ASCII layout and pre-compute shortest-path distances."""
        self.layout = layout
        self.height = len(layout)
        self.width = len(layout[0])
        self.walls = set()
        self.open_cells = []
        self.ninja_start = self.monk_start = None
        self.scroll_spots = []   # every '$' square

        for y, row in enumerate(layout):
            if len(row) != self.width:
                raise ValueError(f"Maze row {y} has the wrong length")
            for x, ch in enumerate(row):
                if ch == "#":
                    self.walls.add((x, y))
                    continue
                self.open_cells.append((x, y))
                if ch == "N":
                    self.ninja_start = (x, y)
                elif ch == "S":
                    self.monk_start = (x, y)
                elif ch == "$":
                    self.scroll_spots.append((x, y))

        if None in (self.ninja_start, self.monk_start) or not self.scroll_spots:
            raise ValueError("Maze needs an N, an S and at least one $")

        # Pre-compute shortest-path distances from every cell to every other
        # cell (BFS). The maze is tiny, so this is instant, and it makes the
        # monk's "chase" move very fast during turbo training.
        self.dist = {cell: self._bfs(cell) for cell in self.open_cells}
        if len(self.dist[self.ninja_start]) != len(self.open_cells):
            raise ValueError("Some floor squares can't be reached")

    def is_wall(self, pos):
        """True if the square at `pos` is a wall."""
        return pos in self.walls

    def valid_actions(self, pos):
        """Actions that don't walk into a wall."""
        return [a for a, (dx, dy) in enumerate(ACTIONS)
                if not self.is_wall((pos[0] + dx, pos[1] + dy))]

    def action_toward(self, start, goal):
        """The action that moves `start` one step along a shortest path to `goal`."""
        goal_dist = self.dist[goal]
        best_action, best_d = None, float("inf")
        for a in self.valid_actions(start):
            dx, dy = ACTIONS[a]
            d = goal_dist[(start[0] + dx, start[1] + dy)]
            if d < best_d:
                best_action, best_d = a, d
        return best_action

    def _bfs(self, source):
        """Breadth-first search: the number of steps from `source` to every reachable square."""
        dist = {source: 0}
        queue = deque([source])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ACTIONS:
                nxt = (x + dx, y + dy)
                if nxt not in self.walls and nxt not in dist:
                    dist[nxt] = dist[(x, y)] + 1
                    queue.append(nxt)
        return dist
