import math

class AIPlayer:
    def __init__(self, problem, depth_limit=2):
        self.problem = problem
        self.depth_limit = depth_limit

    def get_move(self, state, stop_event):
        if stop_event.is_set():
            return None

        def alpha_beta(state, depth_limit, ai_symbol, human_symbol):
            transposition_table = {}

            def order_actions(actions, state, maximizing, ai_symbol, human_symbol):
                winning_actions = []
                blocking_actions = []

                for action in actions:
                    new_state = state.result(action)
                    if new_state.check_win(ai_symbol):
                        return [action]
                    if new_state.check_win(human_symbol):
                        blocking_actions.append(action)

                if blocking_actions:
                    return blocking_actions

                def action_score(action):
                    new_state = state.result(action)
                    return new_state.evaluate(ai_symbol, human_symbol)

                return sorted(actions, key=action_score, reverse=maximizing)

            def hash_state(state):
                return str(state.grid), state.current_player

            def max_value(state, alpha, beta, depth):
                if stop_event.is_set():
                    return None

                key = (hash_state(state), depth)
                if key in transposition_table:
                    return transposition_table[key]

                if state.is_terminal() or depth == depth_limit:
                    score = state.evaluate(ai_symbol, human_symbol)
                    transposition_table[key] = score
                    return score

                value = -math.inf
                actions = order_actions(state.get_actions(), state, True, ai_symbol, human_symbol)
                for action in actions:
                    if stop_event.is_set():
                        return None
                    new_state = state.result(action)
                    score = min_value(new_state, alpha, beta, depth + 1)
                    if score is None:
                        return None
                    value = max(value, score)
                    if value >= beta:
                        break
                    alpha = max(alpha, value)

                transposition_table[key] = value
                return value

            def min_value(state, alpha, beta, depth):
                if stop_event.is_set():
                    return None

                key = (hash_state(state), depth)
                if key in transposition_table:
                    return transposition_table[key]

                if state.is_terminal() or depth == depth_limit:
                    score = state.evaluate(ai_symbol, human_symbol)
                    transposition_table[key] = score
                    return score

                value = math.inf
                actions = order_actions(state.get_actions(), state, False, ai_symbol, human_symbol)
                for action in actions:
                    if stop_event.is_set():
                        return None
                    new_state = state.result(action)
                    score = max_value(new_state, alpha, beta, depth + 1)
                    if score is None:
                        return None
                    value = min(value, score)
                    if value <= alpha:
                        break
                    beta = min(beta, value)

                transposition_table[key] = value
                return value

            best_score = -math.inf
            best_action = None
            actions = order_actions(state.get_actions(), state, True, ai_symbol, human_symbol)
            for action in actions:
                if stop_event.is_set():
                    return None
                new_state = state.result(action)
                score = min_value(new_state, -math.inf, math.inf, 1)
                if score is None:
                    return None
                if score > best_score:
                    best_score = score
                    best_action = action

            return best_action

        return alpha_beta(state, self.depth_limit, self.problem.ai_symbol, self.problem.human_symbol)

"""
Use a clipboard (transposition_table) to avoid recalculating the approved state.

There are order_actions priorities for winning and blocking.

Standard alpha-beta trimming.

Calculate the evaluation score at the leaf nodes (terminals or reach depth_limit).
"""
