import itertools
import numpy as np

class MonteCarloTree():
    def __init__(self):
        self.root = None

    def re_root(self, state):
        if (self.root == None):
            self.root = GameStateNode(state)
        elif (state.to_tuple() in self.root.children_gamestates):
            self.root = self.root.children_gamestates[state.to_tuple()]
        else:
            self.root = GameStateNode(state)

    def back_propogate(self, node, outcome):
        #TODO

    def get_action_pair(self, node):
        #TODO

class Node():
    def __init__(self, state=None, prev_action=None, parent=None):
        self.state = state
        self.teams = state.teams

        self.times_visited = 0.0
        self.wins = 0.0

        self.my_possible_actions = state.get_legal_actions(teams[0])
        self.opp_possible_actions = state.get_legal_actions(teams[1])

        self.parent = parent
        self.prev_action = prev_action
        self.action_pairs = list(itertools.product(self.my_possible_actions, self.opp_possible_actions))
        self.children = {pair : [] for pair in self.action_pairs}

        self.my_action_n = {a : 0 for a in self.my_possible_actions}
        self.opp_action_n = {a : 0 for a in self.opp_possible_actions}

        self.my_uct_score = {a : 1 / len(self.possible_actions) for a in self.my_possible_actions}
        self.opp_uct_score = {a : 1 / len(self.possible_actions) for a in self.opp_possible_actions}

    def calc_uct_score(self, action_pair):
        C = 0.5
        mean = self.wins / self.times_visited
        my_n = self.my_action_n[action_pair[0]]
        opp_n = self.opp_action_n[action_pair[1]]
        my_explore = 2 * C * np.sqrt(2 * np.log(self.times_visited) / my_n)
        opp_explore = 2 * C * np.sqrt(2 * np.log(self.times_visited) / opp_n)


class Node():
	def __init__(self, parent=None):
		self.times_visited = 0.0
		self.wins = 0.0
		self.parent = parent

class GameStateNode(Node):
	def __init__(self, state, parent=None):
		super(GameStateNode, self).__init__(parent)

		self.state = state
		self.teams = gamestate.teams

		self.my_possible_actions = state.get_legal_actions(teams[0])
        self.opp_possible_actions = state.get_legal_actions(teams[1])
        self.action_pairs = list(itertools.product(self.my_possible_actions, self.opp_possible_actions))
        
        self.children_gamestates = {}
        if parent is not None:
            self.parent.parent.children_gamestates[state.to_tuple()] = self


        self.my_uct_score = {a : 1 / len(self.possible_actions) for a in self.my_possible_actions}
        self.opp_uct_score = {a : 1 / len(self.possible_actions) for a in self.opp_possible_actions}


class ActionPairNode(Node):
	def __init__(self, parent):
		super(ActionPairNode, self).__init__(parent)

        self.action_pair = action_pair
        self.uct_score 



self.root = Node(state)
