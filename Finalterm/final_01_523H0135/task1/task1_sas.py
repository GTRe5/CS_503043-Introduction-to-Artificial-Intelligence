"""
=============================================================================
Task 1 – Simulated Annealing Search on a 3-D Surface
=============================================================================
OOP Architecture
────────────────
  State            – A single (x, y) position on the surface + its f-value.
  Problem          – Owns the mathematical surface and can evaluate / plot.
  Schedule  – Callable that returns temperature T at time step t.
  SearchStrategy   – Abstract base; any optimiser must implement .solve().
  SimulatedAnnealing(SearchStrategy) – Concrete SA implementation.
  Solution         – Glues a Problem to a SearchStrategy; single entry point.
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import random
from abc import ABC, abstractmethod
from sympy import symbols, sin, cos, lambdify


# ─────────────────────────────────────────────────────────────────────────────
# STATE  –  a single point in the search space
# ─────────────────────────────────────────────────────────────────────────────
class State:
    """
    Represents one position (x, y) on the 3-D surface.

    Attributes
    ----------
    x, y  : float  – coordinates
    value : float  – f(x, y); set by Problem.evaluate(); None until evaluated
    """

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x: float       = x
        self.y: float       = y
        self.value: float   = None          # filled in by Problem.evaluate()

    # ── helpers ──────────────────────────────────────────────────────────────
    def copy(self) -> "State":
        s       = State(self.x, self.y)
        s.value = self.value
        return s

    def __repr__(self) -> str:
        val = f"{self.value:.4f}" if self.value is not None else "None"
        return f"State(x={self.x:.4f}, y={self.y:.4f}, value={val})"


# ─────────────────────────────────────────────────────────────────────────────
# PROBLEM  –  the environment (surface definition + evaluation + plotting)
# ─────────────────────────────────────────────────────────────────────────────
class Problem(ABC):
    """Abstract base class for any optimisation problem."""

    @abstractmethod
    def evaluate(self, state: State) -> float:
        """Return the objective value for *state* and store it inside state."""

    @abstractmethod
    def get_neighbors(self, state: State, step_size: float,
                      bounds: tuple) -> list:
        """Return all valid neighbor States reachable from *state*."""

    @abstractmethod
    def plot(self, path: list) -> None:
        """Visualise the surface and overlay the search path."""


class FunctionSurface(Problem):
    """
    The 3-D surface defined by:
        f(x, y) = sin(x/8) + cos(y/4) − sin(x·y/16)
                  + cos(x²/16) + sin(y²/8)

    Evaluation and neighbour generation follow the SA requirements:
      • step size π/32 in each of the four cardinal directions
      • domain bounded to [−10, 10] × [−10, 10]
    """

    def __init__(self):
        x, y  = symbols("x y")
        expr  = (sin(x / 8) + cos(y / 4)
                 - sin(x * y / 16)
                 + cos(x**2 / 16)
                 + sin(y**2 / 8))
        self._f = lambdify((x, y), expr, "numpy")

    # ── Problem interface ─────────────────────────────────────────────────────
    def evaluate(self, state: State) -> float:
        state.value = float(self._f(state.x, state.y))
        return state.value

    def get_neighbors(self, state: State,
                      step_size: float = np.pi / 32,
                      bounds: tuple    = (-10.0, 10.0)) -> list:
        """Four cardinal moves; out-of-bounds states are discarded."""
        deltas    = [(step_size, 0), (-step_size, 0),
                     (0, step_size), (0, -step_size)]
        neighbors = []
        lo, hi    = bounds
        for dx, dy in deltas:
            nx, ny = state.x + dx, state.y + dy
            if lo <= nx <= hi and lo <= ny <= hi:
                neighbor = State(nx, ny)
                self.evaluate(neighbor)
                neighbors.append(neighbor)
        return neighbors

    def plot(self, path: list) -> None:
        """Draw the 3-D surface and overlay the SA search path in red."""
        # ── surface mesh ──────────────────────────────────────────────────────
        xs = np.linspace(-10, 10, 100)
        ys = np.linspace(-10, 10, 100)
        X, Y = np.meshgrid(xs, ys)
        Z = self._f(X, Y)

        # ── path coordinates ──────────────────────────────────────────────────
        px = [s.x     for s in path]
        py = [s.y     for s in path]
        pz = [s.value for s in path]

        fig = plt.figure(figsize=(12, 8))
        ax  = fig.add_subplot(111, projection="3d")

        ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.65, linewidth=0)
        ax.plot(px, py, pz, color="red", linewidth=2.0,
                label=f"SA path ({len(path)} steps)")
        ax.scatter([px[-1]], [py[-1]], [pz[-1]],
                   color="yellow", s=60, zorder=5, label="Best found")

        ax.set_title("Simulated Annealing – Search Path on f(x, y)",
                     fontsize=14)
        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("f(x, y)")
        ax.legend()
        plt.tight_layout()
        plt.show()


# ─────────────────────────────────────────────────────────────────────────────
# COOLING SCHEDULE  –  temperature function T(t)
# ─────────────────────────────────────────────────────────────────────────────
class Schedule:
    """
    Logarithmic cooling schedule:  T(t) = max(T_min, 1 / (1 + α·t))

    Parameters
    ----------
    alpha : float – controls how fast the temperature drops (default 0.01)
    t_min : float – temperature floor below which SA stops (default 0.01)
    """

    def __init__(self, alpha: float = 0.01, t_min: float = 0.01):
        self.alpha = alpha
        self.t_min = t_min

    def __call__(self, t: int) -> float:
        return max(self.t_min, 1.0 / (1.0 + self.alpha * t))


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH STRATEGY  –  abstract base; any algorithm plugs in here
# ─────────────────────────────────────────────────────────────────────────────
class SearchStrategy(ABC):
    """
    Abstract optimisation algorithm.

    Subclasses must implement solve(), which receives a Problem and an initial
    State, then returns (best_state, path_of_states).
    """

    @abstractmethod
    def solve(self, problem: Problem,
              initial_state: State,
              max_iter: int) -> tuple:
        """
        Run the algorithm.

        Returns
        -------
        (best : State, path : list[State])
        """


class SimulatedAnnealing(SearchStrategy):
    """
    Simulated Annealing implementation.

    At each iteration t:
      1. Sample a random neighbour next_s.
      2. ΔE = next_s.value − current.value
      3. Accept if ΔE > 0, or with probability exp(ΔE / T(t)).

    Parameters
    ----------
    schedule  : Schedule – temperature function T(t)
    step_size : float           – neighbour distance (default π/32)
    bounds    : tuple           – (low, high) domain limits
    """

    def __init__(self,
                 schedule:  Schedule = None,
                 step_size: float           = np.pi / 32,
                 bounds:    tuple           = (-10.0, 10.0)):
        self.schedule  = schedule or Schedule()
        self.step_size = step_size
        self.bounds    = bounds

    # ── SearchStrategy interface ──────────────────────────────────────────────
    def solve(self, problem: Problem,
              initial_state: State,
              max_iter: int = 100_000) -> tuple:
        """
        Run SA and return (best_state, full_path).
        The path records every *accepted* state transition.
        """
        current = initial_state.copy()
        problem.evaluate(current)

        best = current.copy()
        path = [current.copy()]

        for t in range(1, max_iter + 1):
            T = self.schedule(t)
            if T <= self.schedule.t_min:           # temperature floor reached
                break

            neighbors = problem.get_neighbors(current, self.step_size,
                                               self.bounds)
            if not neighbors:
                break

            next_s  = random.choice(neighbors)
            delta_E = next_s.value - current.value

            # Acceptance criterion
            if delta_E > 0 or random.random() < np.exp(delta_E / T):
                current = next_s
                path.append(current.copy())
                if current.value > best.value:
                    best = current.copy()

        return best, path


# ─────────────────────────────────────────────────────────────────────────────
# SOLUTION  –  single entry point that binds Problem + Strategy
# ─────────────────────────────────────────────────────────────────────────────
class Solution:
    """
    Orchestrates the optimisation run.

    Usage
    -----
    >>> problem  = FunctionSurface()
    >>> strategy = SimulatedAnnealing()
    >>> sol      = Solution(problem, strategy)
    >>> sol.solve()
    >>> sol.plot()
    """

    def __init__(self, problem: Problem, strategy: SearchStrategy,
                 max_iter: int = 100_000):
        self.problem  = problem
        self.strategy = strategy
        self.max_iter = max_iter

        self.best: State       = None
        self.path: list        = []

    def solve(self, initial_state: State = None) -> "Solution":
        """Run the strategy and store the best state and path."""
        start        = initial_state or State(0.0, 0.0)
        self.best, self.path = self.strategy.solve(
            self.problem, start, self.max_iter
        )
        return self                     # fluent interface

    def plot(self) -> None:
        """Delegate visualisation to the Problem."""
        self.problem.plot(self.path)

    def __repr__(self) -> str:
        return (f"Solution(best={self.best}, "
                f"path_length={len(self.path)}, "
                f"strategy={type(self.strategy).__name__})")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # 1. Define the problem
    problem  = FunctionSurface()

    # 2. Choose a cooling schedule and algorithm
    schedule = Schedule(alpha=0.01, t_min=0.01)
    strategy = SimulatedAnnealing(schedule=schedule,
                                   step_size=np.pi / 32,
                                   bounds=(-10.0, 10.0))

    # 3. Create and run the solution
    sol = Solution(problem, strategy, max_iter=100_000)
    print("Running Simulated Annealing …")
    sol.solve(initial_state=State(0.0, 0.0))

    # 4. Report results
    print(f"\n{'─'*50}")
    print(f"  Best state : {sol.best}")
    print(f"  Path steps : {len(sol.path)}")
    print(f"{'─'*50}")

    # 5. Visualise
    sol.plot()


if __name__ == "__main__":
    main()