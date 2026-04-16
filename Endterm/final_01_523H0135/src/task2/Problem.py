class TicTacToeProblem:
    def __init__(self, initial_state, ai_symbol="O"):
        self.initial_state = initial_state
        self.ai_symbol = ai_symbol
        self.human_symbol = "X" if ai_symbol == "O" else "O"

    def actions(self, state):
        return state.get_actions()

    def result(self, state, action):
        return state.result(action)

    def goal_test(self, state):
        return state.is_terminal()

    def utility(self, state):
        return state.utility(self.ai_symbol)
