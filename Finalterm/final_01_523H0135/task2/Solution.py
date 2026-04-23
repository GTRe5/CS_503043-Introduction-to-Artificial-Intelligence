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
  sol.undo()               - revert the last two half-moves (human + AI)
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

import datetime
import glob
import os
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
        self._current_save_path: str | None = None  # track which file was loaded

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
        self._current_save_path = None   # new game → no existing slot to overwrite

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
        if self._ai_thinking or not self._redo_stack:
            return False

        if len(self._redo_stack) >= 2:
            self._history.append(self._redo_stack.pop())
            self._history.append(self._redo_stack.pop())
            return True

        return False


    # ── persistence ───────────────────────────────────────────────────────────
    def save(self, path: str) -> None:
        """Write game state to an explicit path."""
        data = {
            "history":     self._history,
            "depth_limit": self.depth_limit,
            "saved_at":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "move_count":  len(self._history) - 1,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def save_slot(self, folder: str) -> str:
        """
        Save the current game, reusing the same file if this session was
        loaded from an existing slot.

        Behaviour
        ---------
        • New game (never saved before) → creates  save_YYYYMMDD_HHMMSS.pkl
          and remembers the path for all future saves in this session.
        • Resumed game (loaded from a slot) → overwrites that same file so
          no duplicate clone is produced regardless of how many times the
          player pauses and resumes.

        Returns the full path of the save file written.
        """
        os.makedirs(folder, exist_ok=True)
        if self._current_save_path is None:
            # First save for this session – mint a new timestamped slot.
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._current_save_path = os.path.join(folder, f"save_{ts}.pkl")
        self.save(self._current_save_path)
        return self._current_save_path

    @staticmethod
    def list_saves(folder: str) -> list:
        """
        Scan *folder* for save_*.pkl files and return a list of metadata
        dicts sorted newest-first.

        Each dict contains:
          path        – full file path
          saved_at    – human-readable datetime string
          depth_limit – difficulty level stored in the file
          move_count  – number of plies played at save time
        """
        saves = []
        pattern = os.path.join(folder, "save_*.pkl")
        for path in sorted(glob.glob(pattern), reverse=True):
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                saves.append({
                    "path":        path,
                    "saved_at":    data.get("saved_at",    "Unknown date"),
                    "depth_limit": data.get("depth_limit", 3),
                    "move_count":  data.get("move_count",  0),
                })
            except Exception:
                pass
        return saves

    @staticmethod
    def delete_save(path: str) -> None:
        """Delete a save file from disk. Silently ignores missing files."""
        try:
            os.remove(path)
        except Exception:
            pass

    def load(self, path: str) -> bool:
        """
        Load a saved game from *path*.

        On success, remembers *path* as the current save slot so that
        subsequent save_slot() calls overwrite this file instead of
        creating a new clone.

        Returns True on success, False on failure.
        """
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            if not isinstance(data, dict) or "history" not in data:
                return False
            self._history    = data["history"]
            self.depth_limit = data.get("depth_limit", self.depth_limit)
            self._problem    = Problem(self._history[0], ai_symbol=self.ai_symbol)
            self._strategy   = AlphaBetaSearch(self._problem, self.depth_limit)
            self._current_save_path = path   # ← remember slot; no clone on next save
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