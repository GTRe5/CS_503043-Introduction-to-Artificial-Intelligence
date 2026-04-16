import copy

class State:
    def __init__(self, grid=None, current_player="X"):
        self.size = 9
        if grid:
            self.grid = copy.deepcopy(grid)
        else:
            self.grid = [["." for _ in range(self.size)] for _ in range(self.size)]
        self.current_player = current_player

    def __eq__(self, other):
        return isinstance(other, State) and self.grid == other.grid and self.current_player == other.current_player

    def __hash__(self):
        return hash((tuple(tuple(row) for row in self.grid), self.current_player))


    """
    The get_actions(self) function in the State class is responsible for returning the list of valid moves (empty squares).
    Optimize by only considering the empty squares near the existing pieces to reduce the number of moves needed to be checked in the search tree.
    """
    def get_actions(self):
        radius = 2
        actions = set()
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != ".":
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.size and 0 <= nc < self.size and self.grid[nr][nc] == ".":
                                actions.add((nr, nc))
        if not actions:
            return [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == "."]
        return list(actions)

    def result(self, action):
        r, c = action
        new_state = State(self.grid, "O" if self.current_player == "X" else "X")
        new_state.grid[r][c] = self.current_player
        return new_state

    def is_terminal(self):
        return self.check_win("X") or self.check_win("O") or self.is_full()

    def utility(self, ai_symbol):
        if self.check_win(ai_symbol):
            return 10000
        elif self.check_win("O" if ai_symbol == "X" else "X"):
            return -10000
        return 0

    def is_full(self):
        return all(cell != "." for row in self.grid for cell in row)

    def check_win(self, symbol):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != symbol:
                    continue
                for dr, dc in directions:
                    count = 1
                    for step in range(1, 4):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < self.size and 0 <= nc < self.size and self.grid[nr][nc] == symbol:
                            count += 1
                        else:
                            break
                    if count >= 4:
                        return True
        return False

    def display(self):
        print("   " + " ".join(str(i) for i in range(self.size)))
        for idx, row in enumerate(self.grid):
            print(f"{idx:2} " + " ".join(row))

    """
    Scan all sequences of 4 consecutive tokens (horizontal, vertical, diagonal) on the board.
    Evaluate each sequence using the function line_score(...):
        Reward if the AI is about to win.
        Punish if the player is about to win.
        Prioritize tokens close to the center of the board (as they often have more development directions).
    """
    def evaluate(self, ai_symbol, human_symbol):
        def line_score(line):
            ai_count = line.count(ai_symbol)
            human_count = line.count(human_symbol)
            empty_count = line.count(".")

            # If there are both AI and players in one line -> it no longer has value
            if ai_count > 0 and human_count > 0:
                return 0

            # Attack (AI)
            if ai_count == 4:
                return 100000
            elif ai_count == 3 and empty_count == 1:
                return 10000
            elif ai_count == 2 and empty_count == 2:
                return 500
            elif ai_count == 1 and empty_count == 3:
                return 50

            # Defense (The player is about to win)
            if human_count == 4:
                return -100000
            elif human_count == 3 and empty_count == 1:
                return -10000
            elif human_count == 2 and empty_count == 2:
                return -500
            elif human_count == 1 and empty_count == 3:
                return -50

            return 0

        total = 0
        size = self.size

        for r in range(size):
            for c in range(size):
                lines = []

                # Horizontal
                if c + 3 < size:
                    lines.append([self.grid[r][c + i] for i in range(4)])
                # Vertical
                if r + 3 < size:
                    lines.append([self.grid[r + i][c] for i in range(4)])
                # Diagonal \
                if r + 3 < size and c + 3 < size:
                    lines.append([self.grid[r + i][c + i] for i in range(4)])
                # Diagonal /
                if r - 3 >= 0 and c + 3 < size:
                    lines.append([self.grid[r - i][c + i] for i in range(4)])

                for line in lines:
                    total += line_score(line)

        # Priority near the center
        center = size // 2
        for r in range(size):
            for c in range(size):
                if self.grid[r][c] == ai_symbol:
                    total += 5 - (abs(r - center) + abs(c - center))

        return total


    def get_winning_line(self, symbol):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != symbol:
                    continue
                for dr, dc in directions:
                    line = [(r, c)]
                    for step in range(1, 4):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < self.size and 0 <= nc < self.size and self.grid[nr][nc] == symbol:
                            line.append((nr, nc))
                        else:
                            break
                    if len(line) >= 4:
                        return line
        return None
