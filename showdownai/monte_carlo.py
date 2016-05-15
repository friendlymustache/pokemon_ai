import itertools
import numpy as np

class MonteCarloTree():
    def __init__(self):
        self.root = Node()

    def back_propogate(self, node, outcome):
        #TODO

    def get_action_pair(self, node):
        #TODO

class Node():
    def __init__(self, state=NULL, prev_action=NULL, parent=NULL):
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




self.root = Node(state)
