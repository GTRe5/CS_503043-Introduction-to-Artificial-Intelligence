"""
Solution.py
--------
SearchStrategy  -- abstract base class for any search algorithm.
AStarSearch     -- concrete A* implementation with pluggable heuristic.
Solution        -- high-level wrapper.

Heuristic
---------
h(state) = teleport-aware distance to the FARTHEST remaining food pellet.

Admissibility : it is the minimum distance to the last food, so h never
                overestimates the true cost.
Consistency   : each move changes distance by at most 1 → triangle inequality.
"""
from __future__ import annotations
import heapq
from abc import ABC, abstractmethod
from Problem import Problem
from State import Pacman, State


# ---------------------------------------------------------------------------
# Distance helper
# ---------------------------------------------------------------------------

def get_dist_with_teleport(p1: tuple[int,int], p2: tuple[int,int], prob: Problem) -> int:
    """
    Manhattan distance between p1 and p2, accounting for the four inner-corner
    teleport shortcuts.

    Fix vs. original:
    - Uses the same inner-corner pairs as Problem._corner_pairs() instead of
      the outer wall corners (which are always walls and therefore unreachable).
    - Removes the spurious +1 that was added per teleport hop (the teleport
      itself is free; only the step *to* the corner is counted).
    """
    x1, y1 = p1
    x2, y2 = p2

    # Direct Manhattan distance
    min_dist = abs(x1 - x2) + abs(y1 - y2)

    # Check each inner-corner pair as a potential shortcut
    mx = prob.width  - 2
    my = prob.height - 2
    corner_pairs = [
        ((1,  1),  (mx, my)),
        ((mx, 1),  (1,  my)),
    ]

    for (cx, cy), (tx, ty) in corner_pairs:
        # Route: p1 → (cx,cy) → teleport → (tx,ty) → p2
        d1 = abs(x1-cx) + abs(y1-cy) + abs(tx-x2) + abs(ty-y2)
        min_dist = min(min_dist, d1)

        # Route: p1 → (tx,ty) → teleport → (cx,cy) → p2
        d2 = abs(x1-tx) + abs(y1-ty) + abs(cx-x2) + abs(cy-y2)
        min_dist = min(min_dist, d2)

    return min_dist


def heuristic(state: Pacman, problem: Problem) -> int:
    """
    Teleport-aware distance to the FARTHEST remaining food pellet.

    Using the farthest food is more informed than the nearest food while
    remaining admissible and consistent.
    """
    if not state.food:
        return 0
    return max(get_dist_with_teleport(state.pos, f, problem) for f in state.food)


# ---------------------------------------------------------------------------
# Abstract strategy
# ---------------------------------------------------------------------------

class SearchStrategy(ABC):
    @abstractmethod
    def search(self, problem: Problem) -> tuple[list[str] | None, int | None]:
        """Run the search and return (action_list, total_cost)."""


# ---------------------------------------------------------------------------
# A* search
# ---------------------------------------------------------------------------

class AStarSearch(SearchStrategy):
    """
    A* graph search for the Pacman problem.
    Uses a parent-pointer dict for memory-efficient path reconstruction.
    """

    def search(self, problem: Problem) -> tuple[list[str] | None, int | None]:
        start = Pacman(
            pos         = problem.pacman_pos,
            food        = problem.food,
            cost        = 0,
            power_timer = 0,
        )

        came_from: dict[Pacman, tuple[Pacman | None, str | None]] = {start: (None, None)}
        g_score:   dict[Pacman, int] = {start: 0}

        counter  = 0
        frontier = [(heuristic(start, problem), counter, start)]
        closed:  set[Pacman] = set()

        while frontier:
            _, _, current = heapq.heappop(frontier)

            if current in closed:
                continue
            closed.add(current)

            if current.is_goal():
                return self._reconstruct(came_from, current)

            for next_state, action, step_cost in current.get_successors(problem):
                if next_state in closed:
                    continue

                tentative_g = g_score[current] + step_cost
                if next_state not in g_score or tentative_g < g_score[next_state]:
                    g_score[next_state]   = tentative_g
                    came_from[next_state] = (current, action)
                    f = tentative_g + heuristic(next_state, problem)
                    counter += 1
                    heapq.heappush(frontier, (f, counter, next_state))

        return None, None

    @staticmethod
    def _reconstruct(came_from, goal):
        actions = []
        state = goal
        while came_from[state][0] is not None:
            parent, action = came_from[state]
            actions.append(action)
            state = parent
        actions.reverse()
        return actions, goal.cost


# ---------------------------------------------------------------------------
# Solution facade
# ---------------------------------------------------------------------------

class Solution:
    def __init__(self, problem: Problem, strategy: SearchStrategy) -> None:
        self.problem  = problem
        self.strategy = strategy
        self._path    = None
        self._cost    = None
        self._solved  = False

    def solve(self):
        if not self._solved:
            self._path, self._cost = self.strategy.search(self.problem)
            self._solved = True
        return self._path, self._cost

    @property
    def path(self):
        if not self._solved: self.solve()
        return self._path

    @property
    def cost(self):
        if not self._solved: self.solve()
        return self._cost

    @property
    def solved(self):
        return self._solved and self._path is not None

    def print_result(self):
        if self.path is None:
            print('No solution found.')
            return
        print('-' * 50)
        print(f'Actions ({len(self.path)} moves) : {self.path}')
        print(f'Total cost : {self.cost}')
        print('-' * 50)

    def __repr__(self):
        status = f'solved, cost={self._cost}' if self.solved else 'unsolved'
        return f"Solution(strategy={type(self.strategy).__name__}, {status})"