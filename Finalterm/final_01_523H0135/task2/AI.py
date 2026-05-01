"""
AI.py - Search strategy for the Tic-Tac-Toe AI.

Architecture
────────────
  SearchStrategy (ABC)       - any AI algorithm must implement get_move().
  AlphaBetaSearch(Strategy)  - heuristic alpha-beta with:
                                 • transposition table (avoid re-evaluating states)
                                 • move ordering (win-first, block-second, then scored)
                                 • configurable depth limit L
"""

import math
from abc import ABC, abstractmethod


# ─────────────────────────────────────────────────────────────────────────────
# ABSTRACT BASE
# ─────────────────────────────────────────────────────────────────────────────
class SearchStrategy(ABC):
    """Abstract AI strategy. Subclasses implement get_move()."""

    @abstractmethod
    def get_move(self, state, stop_event) -> tuple | None:
        """
        Return the best (row, col) action for the current state.
        stop_event : threading.Event - set externally to cancel search early.
        Returns None if cancelled.
        """


# ─────────────────────────────────────────────────────────────────────────────
# CONCRETE: HEURISTIC ALPHA-BETA SEARCH
# ─────────────────────────────────────────────────────────────────────────────
class AlphaBetaSearch(SearchStrategy):
    """
    Heuristic Alpha-Beta Search (h-minimax).

    Combines standard alpha-beta pruning with a depth limit L and a
    heuristic evaluation function at non-terminal leaf nodes.

    Depth limit rationale
    ---------------------
    Depth 2 (Easy) - looks 2 plies ahead; fast, moderate play.
    Depth 3 (Medium) - looks 3 plies; noticeably stronger.
    Depth 5 (Hard) - looks 5 plies; very strong but still responsive
                     thanks to move ordering and alpha-beta pruning.

    Move ordering rationale
    -----------------------
    Searching winning moves first and blocking moves second causes
    alpha-beta to prune far more branches, effectively doubling the
    useful search depth for the same budget.

    Transposition table
    -------------------
    Maps (board_hash, depth) → evaluated score to avoid re-computing
    identical positions reached via different move sequences.
    """

    def __init__(self, problem, depth_limit: int = 3):
        self.problem     = problem
        self.depth_limit = depth_limit

    # ── public interface ──────────────────────────────────────────────────────
    def get_move(self, state, stop_event) -> tuple | None:
        if stop_event.is_set():
            return None

        ai_sym    = self.problem.ai_symbol
        hu_sym    = self.problem.human_symbol
        tt        = {}                          # transposition table

        # ── helpers ──────────────────────────────────────────────────────────
        def state_key(s, depth):
            return (tuple(tuple(r) for r in s.grid), s.current_player, depth)

        MAX_CANDIDATES = 12   # cap branching factor for speed

        def order_actions(actions, s, maximizing):
            """Win immediately > block opponent win > heuristic score.

            result() is computed ONCE per action and cached to avoid
            redundant deep-copies of the 9×9 grid.
            """
            cache = {a: s.result(a) for a in actions}

            for a in actions:
                if cache[a].check_win(ai_sym):
                    return [a]              # instant win - no need to look further

            blocking = [a for a in actions if cache[a].check_win(hu_sym)]
            if blocking:
                return blocking[:MAX_CANDIDATES]

            scored = sorted(actions,
                            key=lambda a: cache[a].evaluate(ai_sym, hu_sym),
                            reverse=maximizing)
            return scored[:MAX_CANDIDATES]

        # ── alpha-beta ────────────────────────────────────────────────────────
        def max_value(s, alpha, beta, depth):
            if stop_event.is_set():
                return None
            key = state_key(s, depth)
            if key in tt:
                return tt[key]
            if s.is_terminal() or depth == self.depth_limit:
                score = s.evaluate(ai_sym, hu_sym)
                tt[key] = score
                return score

            value = -math.inf
            for a in order_actions(s.get_actions(), s, True):
                if stop_event.is_set():
                    return None
                score = min_value(s.result(a), alpha, beta, depth + 1)
                if score is None:
                    return None
                value = max(value, score)
                if value >= beta:
                    break
                alpha = max(alpha, value)

            tt[key] = value
            return value

        def min_value(s, alpha, beta, depth):
            if stop_event.is_set():
                return None
            key = state_key(s, depth)
            if key in tt:
                return tt[key]
            if s.is_terminal() or depth == self.depth_limit:
                score = s.evaluate(ai_sym, hu_sym)
                tt[key] = score
                return score

            value = math.inf
            for a in order_actions(s.get_actions(), s, False):
                if stop_event.is_set():
                    return None
                score = max_value(s.result(a), alpha, beta, depth + 1)
                if score is None:
                    return None
                value = min(value, score)
                if value <= alpha:
                    break
                beta = min(beta, value)

            tt[key] = value
            return value

        # ── root search ───────────────────────────────────────────────────────
        best_score  = -math.inf
        best_action = None

        for action in order_actions(state.get_actions(), state, True):
            if stop_event.is_set():
                return None
            score = min_value(state.result(action), -math.inf, math.inf, 1)
            if score is None:
                return None
            if score > best_score:
                best_score  = score
                best_action = action

        return best_action


# ── backwards-compatible alias ────────────────────────────────────────────────
class AIPlayer:
    """Thin wrapper kept for legacy callers."""
    def __init__(self, problem, depth_limit: int = 3):
        self._strategy = AlphaBetaSearch(problem, depth_limit)

    def get_move(self, state, stop_event):
        return self._strategy.get_move(state, stop_event)