"""
State.py
--------------
State   -- immutable base class for any search-tree state.
Pacman  -- concrete subclass: pacman position + remaining food + power timer.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from Problem import Problem


class State(ABC):
    """
    Immutable, hashable search-tree state.

    Subclasses must define:
    - is_goal()       -> bool
    - get_successors(problem) -> list[tuple[State, str, int]]
                                             (next_state, action, step_cost)
    """

    @abstractmethod
    def is_goal(self) -> bool:
        """Return True iff this state satisfies the goal condition."""

    @abstractmethod
    def get_successors(self, problem: Problem) -> list[tuple['State', str, int]]:
        """
        Return a list of (next_state, action, step_cost) triples reachable
        from this state given the environment described by *problem*.
        """

    @abstractmethod
    def __hash__(self) -> int: ...

    @abstractmethod
    def __eq__(self, other: object) -> bool: ...


# ---------------------------------------------------------------------------

class Pacman(State):
    """
    Concrete search-tree state for the Pacman maze problem.

    Attributes
    ----------
    pos         : (x, y) — current grid cell of pacman
    food        : frozenset of remaining food positions
    power_timer : steps of wall-pass power remaining  (0 = no power)
    cost        : g(n) — total path cost so far (used by A*)
    """

    __slots__ = ('pos', 'food', 'power_timer', 'cost', '_hash')

    def __init__(
        self,
        pos:         tuple[int, int],
        food:        frozenset[tuple[int, int]],
        cost:        int = 0,
        power_timer: int = 0,
    ) -> None:
        self.pos         = pos
        self.food        = food          # frozenset -> immutable & hashable
        self.power_timer = power_timer
        self.cost        = cost
        # Pre-compute hash once (state is immutable)
        self._hash = hash((self.pos, self.food, self.power_timer))

    # ------------------------------------------------------------------ goal
    def is_goal(self) -> bool:
        """Goal: all food pellets have been collected."""
        return len(self.food) == 0

    # ------------------------------------------------------- successor generation
    def get_successors(self, problem: Problem) -> list[tuple['State', str, int]]:
        successors = []
        x, y = self.pos

        for action, (dx, dy) in problem.ACTIONS.items():
            nx, ny = x + dx, y + dy

            # Check if the move is passable (considering wall-pass power)
            if not problem.is_passable(nx, ny, self.power_timer):
                continue

            # --- TELEPORT LOGIC ---
            # If the next position is a corner, jump to the opposite corner
            final_pos = problem.teleport(nx, ny)

            # --- UPDATE FOOD ---
            # Food is eaten at the ARRIVAL position (after potential teleport)
            new_food = self.food - {final_pos}

            # --- UPDATE POWER TIMER ---
            if final_pos in problem.magic_pies:
                new_power = 5
            else:
                new_power = max(0, self.power_timer - 1)

            next_state = Pacman(
                pos         = final_pos,
                food        = new_food,
                cost        = self.cost + 1,
                power_timer = new_power,
            )
            successors.append((next_state, action, 1))

        return successors

    # ----------------------------------------------------------------- hashing
    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pacman):
            return NotImplemented
        return (self.pos, self.food, self.power_timer) == \
               (other.pos, other.food, other.power_timer)

    # Required by heapq when f-values are equal (tie-break on food remaining)
    def __lt__(self, other: 'Pacman') -> bool:
        return len(self.food) < len(other.food)

    # ----------------------------------------------------------------- display
    def __repr__(self) -> str:
        return (f"Pacman(pos={self.pos}, food_left={len(self.food)}, "
                f"power={self.power_timer}, cost={self.cost})")