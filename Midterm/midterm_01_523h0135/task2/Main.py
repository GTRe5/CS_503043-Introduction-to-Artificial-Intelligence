"""
Main.py
-------
Entry point: loads the map, solves with A*, then animates the solution
in a pygame window.

Controls
--------
Any key   -> start animation after the initial map is displayed
ESC / Q   -> quit at any time
"""
from __future__ import annotations
import sys
import time
import pygame

from Problem  import Problem
from State import Pacman
from Solution import AStarSearch, Solution

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CELL        = 24          # pixels per grid cell
FPS         = 10
INFO_HEIGHT = 50          # extra pixels below the map for info labels

# Colour palette
C_BG        = (  0,   0,   0)   # black background
C_WALL      = (  0,   0, 200)   # blue walls
C_EMPTY     = ( 30,  30,  30)   # dark grey floor
C_FOOD      = (255, 255, 255)   # white food dots
C_PIE       = (255,   0, 255)   # magenta magic pies
C_PACMAN    = (255, 220,   0)   # yellow pacman
C_POWER     = (255, 140,   0)   # orange tint when powered-up
C_TEXT      = (200, 200, 200)
C_LABEL_PIE = (255,   0, 255)
C_LABEL_FD  = (255, 255, 255)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class Renderer:
    """Handles all pygame drawing for the Pacman game."""

    def __init__(self, problem: Problem) -> None:
        self.problem = problem
        self.font_sm = None    # initialised after pygame.init()

    def init(self) -> pygame.Surface:
        """Create and return the pygame display surface."""
        pygame.init()
        pygame.display.set_caption('Pacman — A* Search')
        self.font_sm = pygame.font.SysFont('monospace', 14)
        w = self.problem.width  * CELL
        h = self.problem.height * CELL + INFO_HEIGHT
        return pygame.display.set_mode((w, h))

    def draw(
        self,
        screen:      pygame.Surface,
        pacman_pos:  tuple[int, int],
        food:        set[tuple[int, int]],
        pies:        set[tuple[int, int]],
        power_timer: int,
        move_num:    int,
        total_moves: int,
    ) -> None:
        screen.fill(C_BG)
        prob = self.problem

        # ---- map cells ----
        for y, row in enumerate(prob.map_data):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)

                if cell == '%':
                    pygame.draw.rect(screen, C_WALL, rect)
                else:
                    pygame.draw.rect(screen, C_EMPTY, rect)

                    if (x, y) in food:
                        # draw food as a small circle
                        pygame.draw.circle(screen, C_FOOD, rect.center, CELL // 6)

                    if (x, y) in pies:
                        # draw pie as a diamond
                        cx, cy = rect.center
                        r = CELL // 3
                        pygame.draw.polygon(
                            screen, C_PIE,
                            [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
                        )

        # ---- pacman ----
        px, py = pacman_pos
        pac_rect = pygame.Rect(px * CELL, py * CELL, CELL, CELL)
        pac_color = C_POWER if power_timer > 0 else C_PACMAN
        pygame.draw.circle(screen, pac_color, pac_rect.center, CELL // 2 - 1)

        # ---- info bar ----
        bar_y  = prob.height * CELL + 4
        labels = [
            (C_LABEL_PIE, 'O = magic pie (wall-pass x5)'),
            (C_LABEL_FD,  '. = food pellet'),
            (C_TEXT,      f'Move {move_num}/{total_moves}   power={power_timer}'),
        ]
        for i, (colour, text) in enumerate(labels):
            surf = self.font_sm.render(text, True, colour)
            screen.blit(surf, (8, bar_y + i * 16))

        pygame.display.flip()


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------

def replay(
    screen:   pygame.Surface,
    renderer: Renderer,
    problem:  Problem,
    path:     list[str],
    clock:    pygame.time.Clock,
) -> None:
    """Animate the solution step by step."""
    pacman_pos  = problem.pacman_pos
    food        = set(problem.food)
    pies        = set(problem.magic_pies)
    power_timer = 0
    total       = len(path)

    # direction -> (dx, dy)
    DIRS = Problem.ACTIONS

    for move_num, action in enumerate(path, start=1):
        # --- handle quit events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit()

        dx, dy     = DIRS[action]
        nx, ny     = pacman_pos[0] + dx, pacman_pos[1] + dy
        nx, ny     = problem.teleport(nx, ny)
        pacman_pos = (nx, ny)

        power_timer = max(0, power_timer - 1)

        if pacman_pos in food:
            food.remove(pacman_pos)
        if pacman_pos in pies:
            pies.remove(pacman_pos)
            power_timer = 5

        renderer.draw(screen, pacman_pos, food, pies, power_timer, move_num, total)
        clock.tick(FPS)
        time.sleep(1.0 / FPS)

    # ---- hold final frame ----
    print('Done! Press any key or close the window to exit.')
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                waiting = False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def wait_for_keypress(screen: pygame.Surface, renderer: Renderer, problem: Problem) -> None:
    """Draw the initial map and block until the user presses a key."""
    renderer.draw(screen, problem.pacman_pos,
                  set(problem.food), set(problem.magic_pies), 0, 0, 0)
    print('Press any key in the pygame window to start animation...')
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                return


def main(map_file: str = 'task02_pacman_example_map.txt') -> None:
    # ---- load & solve ----
    problem  = Problem(map_file).load()
    solution = Solution(problem, AStarSearch())

    print(f'Loaded  : {problem}')
    print('Solving ...')
    path, cost = solution.solve()
    solution.print_result()

    if path is None:
        return

    # ---- pygame setup ----
    renderer = Renderer(problem)
    screen   = renderer.init()
    clock    = pygame.time.Clock()

    # ---- wait for user to press a key, then animate ----
    wait_for_keypress(screen, renderer, problem)
    replay(screen, renderer, problem, path, clock)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    map_path = sys.argv[1] if len(sys.argv) > 1 else 'task02_pacman_example_map.txt'
    main(map_path)