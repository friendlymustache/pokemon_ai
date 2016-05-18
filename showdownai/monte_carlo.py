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

    def select_add_actionpair(self):
        current = self.root

        my_action = max(current.my_actions, key=lambda i: current.my_actions[i])
        opp_action = max(current.opp_actions, key=lambda i: current.opp_actions[i])
        key = (my_action, opp_action)

        while (key in current.children_actionpairs):
            actionpair_node = current.children_actionpairs[key]

            # TODO: 0 for now, change when non-deterministic
            current = actionpair_node.children_gamestates[0]

            my_action = max(current.my_actions, key=itemgetter(1))[0]
            opp_action = max(current.opp_actions, key=itemgetter(1))[0]
            key = (my_action, opp_action)

        new_actionpair = ActionPairNode(current, key)
        current.children_actionpairs[key] = new_actionpair

        return new_actionpair

    def add_gamestate(self, actionpair_node, new_state): 
        new_gamestate = GameStateNode(state, actionpair_node)
        actionpair_node.children_gamestates.append(new_gamestate)
        return new_gamestate

    def back_propogate(self, node, outcome):
        # Node passed in is a GS node
        while(node.parent != None):
            # Parent is action node; increment, get action pair to calculate uct
            node = node.parent
            node.increment(outcome)
            ap = node.action_pair

            # Update corresponding UCT score in previous GS node
            node = node.parent
            node.increment(outcome, ap)
            node.update_uct_scores(ap)



class Node():
    def __init__(self, parent=None):
        self.times_visited = 0.0
        self.wins = 0.0
        self.parent = parent

    def increment(self, outcome):
        self.times_visited += 1
        self.wins += outcome


class GameStateNode(Node):
    def __init__(self, state, parent=None):
        super(GameStateNode, self).__init__(parent)

        self.state = state
        self.teams = gamestate.teams

        self.my_actions_n = {a: [0.0, 0.0] for a in state.get_legal_actions(teams[0])}
        self.opp_actions_n = {b: [0.0, 0.0] for b in state.get_legal_actions(teams[1])}

        # {action : uct_score}
        self.my_actions = {a : float("inf") for a in state.get_legal_actions(teams[0])}
        self.opp_actions = {b : float("inf") for b in state.get_legal_actions(teams[1])}

        # {(my_action, opp_action) : action pair node}
        self.children_actionpairs = {}

        # {(game_state_tuple) : game_state_node}
        self.children_gamestates = {}
        if parent is not None:
            self.parent.parent.children_gamestates[state.to_tuple()] = self

    def increment(self, outcome, action_pair):
        self.times_visited += 1
        self.wins += outcome
        self.my_actions_n[action_pair[0]][0] += outcome
        self.opp_actions_n[action_pair[1]][0] += outcome
        self.my_actions_n[action_pair[0]][1] += 1
        self.opp_actions_n[action_pair[1]][1] += 1

    def update_uct_scores(self, action_pair, mean):
        C = 0.5

        my_action = action_pair[0]
        opp_action = action_pair[1]

        my_n = self.my_actions_n[my_action][1]
        opp_n = self.opp_actions_n[opp_action][1]

        my_mean = self.my_actions_n[my_action][0] / my_n
        opp_mean = self.opp_actions_n[opp_action][0] / opp_n

        my_explore = 2 * C * np.sqrt(2 * np.log(self.times_visited) / my_n)
        opp_explore = 2 * C * np.sqrt(2 * np.log(self.times_visited) / opp_n)

        self.my_actions[my_action] = my_mean + my_explore
        self.opp_actions[opp_action] = opp_mean + opp_explore


class ActionPairNode(Node):
    def __init__(self, parent, action_pair):
        super(ActionPairNode, self).__init__(parent)

        self.action_pair = action_pair
        self.children_gamestates = []



self.root = Node(state)
