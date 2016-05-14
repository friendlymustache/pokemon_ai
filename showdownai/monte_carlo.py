class MonteCarloTree():
    def __init__(self, state):
        self.root = 

class Node():
    def __init__(self, state, who, action=NULL):
        self.state = state
        self.who = who
        self.possible_actions = state.get_legal_actions(who)
        self.action = action
        self.ucb_score = 1 / self.possible_actions


self.root = Node(state)
