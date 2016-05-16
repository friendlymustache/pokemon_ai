import itertools
import numpy as np
from operator import itemgetter

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

    def select_and_expand(self):
        current = self.root

        my_action = max(current.my_actions, key=itemgetter(1))[0]
        opp_action = max(current.opp_actions, key=itemgetter(1))[0]
        key = (my_action, opp_action)

        while (key in current.children_actionpairs):
            actionpair_node = current.children_actionpairs[key]

            # TODO: 0 for now, change when non-deterministic
            current = actionpair_node.children_gamestates[0]

            my_action = max(current.my_actions, key=itemgetter(1))[0]
            opp_action = max(current.opp_actions, key=itemgetter(1))[0]
            key = (my_action, opp_action)

        current.children_actionpairs[key] = ActionPairNode(current, key)



    def back_propogate(self, node, outcome):
        #TODO

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

        # [(action, uct_score)]
        self.my_actions = [(a, float("inf")) for a in state.get_legal_actions(teams[0])]
        self.opp_actions = [(b, float("inf")) for b in state.get_legal_actions(teams[1])]

        # {(my_action, opp_action) : action pair node}
        self.children_actionpairs = {}

        # {(game_state_tuple) : game_state_node}
        self.children_gamestates = {}
        if parent is not None:
            self.parent.parent.children_gamestates[state.to_tuple()] = self


class ActionPairNode(Node):
    def __init__(self, parent, action_pair):
        super(ActionPairNode, self).__init__(parent)

        self.action_pair = action_pair
        self.children_gamestates = []



self.root = Node(state)
