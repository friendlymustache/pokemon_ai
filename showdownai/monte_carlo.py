class MonteCarloTree():
    def __init__(self, state):
        self.root = 

class Node():
    def __init__(self, state, parent):
        self.state = state
        self.possible_actions = state.get_legal_actions(who)
        self.parent = parent
        self.children = []
        self.my_ucb_score = 1 / len(self.possible_actions)
        self.their_ucb_score = 1 / len(self.possible_actions)


self.root = Node(state)
