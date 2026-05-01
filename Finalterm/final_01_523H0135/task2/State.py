import copy


class State:
    """
    One snapshot of the 9x9 Tic-Tac-Toe board.

    Attributes
    ----------
    grid           : list[list[str]]  - '.' = empty, 'X' / 'O' = played
    current_player : str              - whose turn it is ('X' or 'O')
    size           : int              - board dimension (9)
    WIN_LENGTH     : int              - consecutive pieces needed to win (4)
    """

    SIZE       = 9
    WIN_LENGTH = 4

    def __init__(self, grid=None, current_player: str = "X"):
        self.size           = self.SIZE
        self.current_player = current_player
        self.grid           = (copy.deepcopy(grid)
                               if grid
                               else [["." for _ in range(self.size)]
                                     for _ in range(self.size)])

    # ── equality / hashing (for transposition table) ──────────────────────────
    def __eq__(self, other):
        return (isinstance(other, State)
                and self.grid == other.grid
                and self.current_player == other.current_player)

    def __hash__(self):
        return hash((tuple(tuple(r) for r in self.grid), self.current_player))

    # ── actions ───────────────────────────────────────────────────────────────
    def get_actions(self) -> list:
        """
        Return valid (row, col) moves.
        Restricts candidates to cells within radius 1 of existing pieces
        to keep the search tree manageable on a 9x9 board.
        Falls back to a wider radius-2 scan when radius-1 yields nothing.
        """
        for radius in (1, 2):
            actions = set()
            for r in range(self.size):
                for c in range(self.size):
                    if self.grid[r][c] == ".":
                        continue
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.size and 0 <= nc < self.size
                                    and self.grid[nr][nc] == "."):
                                actions.add((nr, nc))
            if actions:
                return list(actions)

        # Fallback: board is empty - offer only center area
        center = self.size // 2
        return [(r, c)
                for r in range(center - 2, center + 3)
                for c in range(center - 2, center + 3)
                if self.grid[r][c] == "."]

    # ── transitions ───────────────────────────────────────────────────────────
    def result(self, action: tuple) -> "State":
        """Return the new State after placing current_player at *action*."""
        r, c       = action
        next_player = "O" if self.current_player == "X" else "X"
        new_state  = State(self.grid, next_player)
        new_state.grid[r][c] = self.current_player
        return new_state

    # ── terminal checks ───────────────────────────────────────────────────────
    def is_terminal(self) -> bool:
        return self.check_win("X") or self.check_win("O") or self.is_full()

    def is_full(self) -> bool:
        return all(cell != "." for row in self.grid for cell in row)

    def check_win(self, symbol: str) -> bool:
        """True if *symbol* has WIN_LENGTH in a row in any direction."""
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != symbol:
                    continue
                for dr, dc in directions:
                    count = 1
                    for step in range(1, self.WIN_LENGTH):
                        nr, nc = r + dr * step, c + dc * step
                        if (0 <= nr < self.size and 0 <= nc < self.size
                                and self.grid[nr][nc] == symbol):
                            count += 1
                        else:
                            break
                    if count >= self.WIN_LENGTH:
                        return True
        return False

    def get_winning_line(self, symbol: str) -> list | None:
        """Return the list of (row, col) forming the winning line, or None."""
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != symbol:
                    continue
                for dr, dc in directions:
                    line = [(r, c)]
                    for step in range(1, self.WIN_LENGTH):
                        nr, nc = r + dr * step, c + dc * step
                        if (0 <= nr < self.size and 0 <= nc < self.size
                                and self.grid[nr][nc] == symbol):
                            line.append((nr, nc))
                        else:
                            break
                    if len(line) >= self.WIN_LENGTH:
                        return line
        return None

    # ── heuristic evaluation ─────────────────────────────────────────────────
    def evaluate(self, ai_symbol: str, human_symbol: str) -> float:
        """
        Score the board from the AI's perspective.

        Scans all length-4 windows in 4 directions and applies line_score().
        Adds a center-proximity bonus for AI pieces.

        Heuristic rationale
        -------------------
        • A window with both symbols is worthless (0).
        • Fully AI windows score highly (attack); fully human windows score
          negatively (defense urgency).
        • Weights are exponential so imminent threats always outrank distant ones.
        • Center bonus nudges the AI toward the middle where lines cross more.
        """
        def line_score(line: list) -> float:
            ai_cnt    = line.count(ai_symbol)
            hu_cnt    = line.count(human_symbol)
            em_cnt    = line.count(".")

            if ai_cnt > 0 and hu_cnt > 0:
                return 0.0                       # mixed window → no value

            # ── attack ───────────────────────────────────────────────────────
            if ai_cnt == 4:              return  100_000
            if ai_cnt == 3 and em_cnt:  return   10_000
            if ai_cnt == 2 and em_cnt:  return      500
            if ai_cnt == 1 and em_cnt:  return       50

            # ── defence ──────────────────────────────────────────────────────
            if hu_cnt == 4:              return -100_000
            if hu_cnt == 3 and em_cnt:  return  -10_000
            if hu_cnt == 2 and em_cnt:  return     -500
            if hu_cnt == 1 and em_cnt:  return      -50
            return 0.0

        total  = 0.0
        size   = self.size

        for r in range(size):
            for c in range(size):
                # Horizontal
                if c + 3 < size:
                    total += line_score([self.grid[r][c + i] for i in range(4)])
                # Vertical
                if r + 3 < size:
                    total += line_score([self.grid[r + i][c] for i in range(4)])
                # Diagonal ↘
                if r + 3 < size and c + 3 < size:
                    total += line_score([self.grid[r + i][c + i] for i in range(4)])
                # Diagonal ↗
                if r - 3 >= 0 and c + 3 < size:
                    total += line_score([self.grid[r - i][c + i] for i in range(4)])

        # Center-proximity bonus for AI pieces
        center = size // 2
        for r in range(size):
            for c in range(size):
                if self.grid[r][c] == ai_symbol:
                    total += 5 - (abs(r - center) + abs(c - center))

        return total

    def utility(self, ai_symbol: str) -> float:
        human_symbol = "O" if ai_symbol == "X" else "X"
        if self.check_win(ai_symbol):    return  10_000
        if self.check_win(human_symbol): return -10_000
        return 0.0

    # ── debug display ────────────────────────────────────────────────────────
    def display(self) -> None:
        print("   " + " ".join(str(i) for i in range(self.size)))
        for idx, row in enumerate(self.grid):
            print(f"{idx:2} " + " ".join(row))