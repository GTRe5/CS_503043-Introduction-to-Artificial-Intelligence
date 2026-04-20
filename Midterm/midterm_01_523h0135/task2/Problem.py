"""
Problem.py
-------------
Problem  -- the static environment: map grid, food positions, magic-pie
            positions, pacman start, and all spatial queries.
"""
from __future__ import annotations


class Problem:
    ACTIONS: dict[str, tuple[int, int]] = {
        'North': ( 0, -1),
        'South': ( 0,  1),
        'East' : ( 1,  0),
        'West' : (-1,  0),
    }

    def __init__(self, file_path: str) -> None:
        self.file_path   = file_path
        self.map_data:   list[list[str]] = []
        self.pacman_pos  = None
        self.food        = frozenset()
        self.magic_pies  = frozenset()
        self._width      = 0
        self._height     = 0

    def load(self) -> 'Problem':
        food_set, pie_set = set(), set()
        with open(self.file_path, 'r') as fh:
            for y, raw_line in enumerate(fh):
                row = []
                for x, ch in enumerate(raw_line.rstrip('\n')):
                    row.append(ch)
                    if   ch == 'P': self.pacman_pos = (x, y)
                    elif ch == '.': food_set.add((x, y))
                    elif ch == 'O': pie_set.add((x, y))
                self.map_data.append(row)
        self._height    = len(self.map_data)
        self._width     = max(len(r) for r in self.map_data)
        self.food       = frozenset(food_set)
        self.magic_pies = frozenset(pie_set)
        if self.pacman_pos is None:
            raise ValueError(f"No 'P' found in map: {self.file_path}")
        return self

    @property
    def width(self):  return self._width
    @property
    def height(self): return self._height

    def in_bounds(self, x, y):
        return 0 <= x < self._width and 0 <= y < self._height

    def get_cell(self, x, y):
        if self.in_bounds(x, y):
            row = self.map_data[y]
            return row[x] if x < len(row) else ' '
        return '%'

    def is_wall(self, x, y):
        return self.get_cell(x, y) == '%'

    def _corner_pairs(self):
        """
        Teleport pairs using INNER corner cells (offset 1 from each edge).

        Bug fix: original code used actual grid corners (0,0) etc., which are
        always '%' walls — pacman could never reach them, so teleportation was
        effectively disabled.  Inner cells (1,1), (W-2,1), (1,H-2), (W-2,H-2)
        are the first passable positions near each corner.

        Pairs:  (1,1) <-> (W-2, H-2)   and   (W-2,1) <-> (1, H-2)
        """
        mx = self._width  - 2
        my = self._height - 2
        return [
            ((1,  1),  (mx, my)),
            ((mx, 1),  (1,  my)),
        ]

    def is_corner(self, x, y):
        for c1, c2 in self._corner_pairs():
            if (x, y) == c1 or (x, y) == c2:
                return True
        return False

    def teleport(self, x, y):
        for c1, c2 in self._corner_pairs():
            if (x, y) == c1: return c2
            if (x, y) == c2: return c1
        return (x, y)

    def is_passable(self, x, y, power_timer):
        if not self.in_bounds(x, y):
            return False
        return not self.is_wall(x, y) or power_timer > 0

    def __repr__(self):
        return (f"Problem(file='{self.file_path}', "
                f"size={self._width}x{self._height}, "
                f"food={len(self.food)}, pies={len(self.magic_pies)})")