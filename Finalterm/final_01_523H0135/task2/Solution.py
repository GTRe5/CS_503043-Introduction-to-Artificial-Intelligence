"""
Solution.py - Single entry point for game logic.

The Solution class binds a Problem (rules) and a SearchStrategy (AI)
and owns all game-state transitions.  The UI (main.py) only calls
Solution methods — it never touches State or Problem directly.

Public API
──────────
  sol.reset()              - start a fresh game
  sol.human_move(r, c)     - apply the human's move; returns new State or None
  sol.request_ai_move()    - launch AI search in background thread
  sol.apply_ai_move()      - apply the pending AI move; returns new State or None
  sol.undo()               - revert the last half-move (one ply at a time)
  sol.redo()               - reapply the last undone pair of half-moves (human + AI)
  sol.save(path)           - pickle current history
  sol.load(path)           - restore history from pickle

Read-only properties
────────────────────
  sol.state                - current State
  sol.is_over              - True if the game has ended
  sol.winner               - 'X', 'O', 'Draw', or None
  sol.winning_line         - list of (row, col) or None
  sol.ai_thinking          - True while background thread is running
  sol.difficulty_name      - 'Easy' / 'Medium' / 'Hard'
"""

import pickle
import threading

from State   import State
from Problem import Problem
from AI      import AlphaBetaSearch, SearchStrategy


class Solution:
    """
    Orchestrates a full game session.

    Parameters
    ----------
    depth_limit : int - AI search depth (2=Easy, 3=Medium, 5=Hard)
    ai_symbol   : str - 'O' (AI goes second, human plays X)
    """

    DEPTH_NAMES = {2: "Easy", 3: "Medium", 5: "Hard"}

    def __init__(self, depth_limit: int = 3, ai_symbol: str = "O"):
        self.depth_limit = depth_limit
        self.ai_symbol   = ai_symbol

        self._history:    list  = []
        self._problem:    Problem        = None
        self._strategy:   SearchStrategy = None

        self._ai_result   = None          # pending move from background thread
        self._ai_thinking = False
        self._stop_event  = threading.Event()
        self._ai_thread:  threading.Thread = None

        self._redo_stack = []

        self.reset()

    # ── setup ─────────────────────────────────────────────────────────────────
    def reset(self) -> None:
        """Start a fresh game with the current difficulty."""
        self._stop_ai()
        initial          = State()
        self._problem    = Problem(initial, ai_symbol=self.ai_symbol)
        self._strategy   = AlphaBetaSearch(self._problem, self.depth_limit)
        self._history    = [initial]
        self._ai_result  = None
        self._stop_event = threading.Event()
        self._redo_stack = []

    def set_difficulty(self, depth_limit: int) -> None:
        self.depth_limit = depth_limit

    # ── read-only properties ──────────────────────────────────────────────────
    @property
    def state(self) -> State:
        return self._history[-1]

    @property
    def is_over(self) -> bool:
        return self._problem.goal_test(self.state)

    @property
    def winner(self) -> str | None:
        if not self.is_over:
            return None
        for sym in ("X", "O"):
            if self.state.check_win(sym):
                return sym
        return "Draw"

    @property
    def winning_line(self) -> list | None:
        if not self.is_over:
            return None
        for sym in ("X", "O"):
            line = self.state.get_winning_line(sym)
            if line:
                return line
        return None

    @property
    def ai_thinking(self) -> bool:
        return self._ai_thinking

    @property
    def difficulty_name(self) -> str:
        return self.DEPTH_NAMES.get(self.depth_limit, str(self.depth_limit))

    @property
    def current_player(self) -> str:
        return self.state.current_player

    # ── human move ────────────────────────────────────────────────────────────
    def human_move(self, row: int, col: int) -> State | None:
        """
        Apply (row, col) as the human's move.
        Returns the resulting State, or None if the move is invalid.
        """
        if self.is_over or self._ai_thinking:
            return None
        if self.state.current_player != self._problem.human_symbol:
            return None
        if (row, col) not in self.state.get_actions():
            return None

        next_state = self.state.result((row, col))
        self._history.append(next_state)
        self._redo_stack.clear()
        return next_state

    # ── AI move ───────────────────────────────────────────────────────────────
    def request_ai_move(self) -> None:
        """Launch the AI search in a background thread."""
        if self.is_over or self._ai_thinking:
            return
        self._ai_thinking = True
        self._ai_result   = None
        snapshot          = self.state          # capture before thread starts

        def _worker():
            self._ai_result   = self._strategy.get_move(snapshot, self._stop_event)
            self._ai_thinking = False

        self._ai_thread = threading.Thread(target=_worker, daemon=True)
        self._ai_thread.start()

    def apply_ai_move(self) -> State | None:
        """
        Call from the main loop once ai_thinking is False.
        Applies the pending AI move and returns the new State, or None.
        """
        if self._ai_thinking or self._ai_result is None:
            return None

        action           = self._ai_result
        self._ai_result  = None

        if self.is_over:
            return None
        if action not in self.state.get_actions():
            return None

        next_state = self.state.result(action)
        self._history.append(next_state)
        self._redo_stack.clear()
        return next_state

    # ── undo ──────────────────────────────────────────────────────────────────
    def undo(self) -> bool:
        """
        Revert the last two half-moves (AI reply + human move).
        Returns True if undo was possible.
        """
        if self._ai_thinking or len(self._history) <= 1:
            return False

        self._redo_stack.append(self._history.pop())
        return True
    
    # ── redo ──────────────────────────────────────────────────────────────────
    def redo(self) -> bool:
        """
        Reapply the last two undone half-moves (human move + AI reply).

        Redo is only possible when:
          • the AI is not currently thinking, and
          • there are at least two states on the redo stack
            (one human ply + one AI ply that were previously undone).

        The redo stack is cleared automatically whenever a new human or AI
        move is applied, so redo is unavailable once the player makes a
        fresh move after undoing.

        Returns True if redo was applied, False otherwise.
        """
        if self._ai_thinking or not self._redo_stack:
            return False

        if len(self._redo_stack) >= 2:
            self._history.append(self._redo_stack.pop())
            self._history.append(self._redo_stack.pop())
            return True

        return False


    # ── persistence ───────────────────────────────────────────────────────────
    def save(self, path: str) -> None:
        data = {"history": self._history, "depth_limit": self.depth_limit}
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str) -> bool:
        """Load a saved game. Returns True on success."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            if not isinstance(data, dict) or "history" not in data:
                return False
            self._history    = data["history"]
            self.depth_limit = data.get("depth_limit", self.depth_limit)
            self._problem    = Problem(self._history[0], ai_symbol=self.ai_symbol)
            self._strategy   = AlphaBetaSearch(self._problem, self.depth_limit)
            return True
        except Exception:
            return False

    # ── internal ──────────────────────────────────────────────────────────────
    def _stop_ai(self) -> None:
        self._stop_event.set()
        if self._ai_thread and self._ai_thread.is_alive():
            self._ai_thread.join(timeout=1)
        self._ai_thinking = False

    def shutdown(self) -> None:
        """Call before quitting to cleanly stop the AI thread."""
        self._stop_ai()