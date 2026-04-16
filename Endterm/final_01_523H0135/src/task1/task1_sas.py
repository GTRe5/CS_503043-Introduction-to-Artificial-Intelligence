import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, sin, cos, lambdify
import random
from abc import ABC, abstractmethod

#========== Abstract Problem Class ==========
class Problem(ABC):
    @abstractmethod
    def evaluate(self, solution):
        pass

    @abstractmethod
    def plot(self, path):
        pass

#========== Concrete Problem: Function Surface ==========
class FunctionSurface(Problem):
    def __init__(self):
        x, y = symbols('x y')
        expr = sin(x / 8) + cos(y / 4) - sin(x * y / 16) + cos(x**2 / 16) + sin(y**2 / 8)
        self.f = lambdify((x, y), expr, 'numpy')

    def evaluate(self, solution):
        return self.f(solution.x, solution.y)

    def plot(self, path):
        X = np.linspace(-10, 10, 50)
        Y = np.linspace(-10, 10, 50)
        X, Y = np.meshgrid(X, Y)
        Z = self.f(X, Y)

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.7)

        x_points = [s.x for s in path]
        y_points = [s.y for s in path]
        z_points = [self.evaluate(s) for s in path]

        ax.plot(x_points, y_points, z_points, color='red', linewidth=2)
        plt.title("Simulated Annealing Search Path")
        plt.tight_layout()
        plt.show()

#========== Solution Class ==========
class Solution:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
        self.value = None

    def __str__(self):
        return f"Solution(x={self.x:.4f}, y={self.y:.4f}, value={self.value:.4f})" if self.value is not None else \
               f"Solution(x={self.x:.4f}, y={self.y:.4f}, value=None)"

    def copy(self):
        s = Solution(self.x, self.y)
        s.value = self.value
        return s

#========== Optimization Algorithm Base Class ==========
class OptimizationAlgorithm(ABC):
    def __init__(self, problem):
        self.problem = problem

    @abstractmethod
    def solve(self):
        pass

#========== Cooling Schedule ==========
class Schedule:
    def __call__(self, t):
        return max(0.01, 1.0 / (1.0 + 0.01 * t))

#========== Simulated Annealing ==========
class SimulatedAnnealing(OptimizationAlgorithm):
    def __init__(self, problem, schedule=None, step_size=np.pi/32, bounds=(-10, 10)):
        super().__init__(problem)
        self.schedule = schedule or Schedule()
        self.step_size = step_size
        self.bounds = bounds

    def get_neighbors(self, solution):
        directions = [(self.step_size, 0), (-self.step_size, 0),
                      (0, self.step_size), (0, -self.step_size)]
        neighbors = []

        for dx, dy in directions:
            nx, ny = solution.x + dx, solution.y + dy
            if self.bounds[0] <= nx <= self.bounds[1] and self.bounds[0] <= ny <= self.bounds[1]:
                neighbor = Solution(nx, ny)
                neighbor.value = self.problem.evaluate(neighbor)
                neighbors.append(neighbor)

        return neighbors

    def solve(self, max_iter=100000, initial_solution=None):
        current = initial_solution or Solution()
        current.value = self.problem.evaluate(current)

        best = current.copy()
        path = [current.copy()]

        for t in range(1, max_iter + 1):
            T = self.schedule(t)
            if T < 0.0001:
                break

            neighbors = self.get_neighbors(current)
            if not neighbors:
                break

            next_sol = random.choice(neighbors)
            delta_E = next_sol.value - current.value

            if delta_E > 0 or random.random() < np.exp(delta_E / T):
                current = next_sol
                path.append(current.copy())
                if current.value > best.value:
                    best = current.copy()

        return best, path

#========== Main ==========
def main():
    problem = FunctionSurface()
    sa = SimulatedAnnealing(problem)
    print("Running simulated annealing...")
    best_solution, path = sa.solve()
    print(f"Best solution found: {best_solution}")
    problem.plot(path)

if __name__ == "__main__":
    main()
