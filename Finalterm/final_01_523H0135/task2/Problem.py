from State import State


class Problem:
    """
    Defines the 9x9 Tic-Tac-Toe game from the AI's perspective.

    Attributes
    ----------
    initial_state : State - fresh board
    ai_symbol     : str   - the symbol the AI plays ('O' by default)
    human_symbol  : str   - the opposing symbol
    """

    def __init__(self, initial_state: State = None, ai_symbol: str = "O"):
        self.initial_state = initial_state or State()
        self.ai_symbol     = ai_symbol
        self.human_symbol  = "X" if ai_symbol == "O" else "O"

    # ── standard problem interface ────────────────────────────────────────────
    def actions(self, state: State) -> list:
        return state.get_actions()

    def result(self, state: State, action: tuple) -> State:
        return state.result(action)

    def goal_test(self, state: State) -> bool:
        return state.is_terminal()

    def utility(self, state: State) -> float:
        return state.utility(self.ai_symbol)