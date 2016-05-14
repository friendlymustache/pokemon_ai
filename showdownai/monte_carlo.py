class MonteCarlo():
    def __init__(self, state):
        self.root = Node(state)



class Node():
    def __init__(self, state, action=NULL):
        self.state = state
        self.action = action


