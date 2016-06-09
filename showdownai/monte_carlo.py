import itertools
from copy import deepcopy
import numpy as np
from operator import itemgetter
from classifier import Classifier

class MonteCarloTree():
    def __init__(self, sl_files, rollout_files, value_files):
        self.root = None
        self.sl_classifier = Classifier(sl_files[0], sl_files[1], sl_files[2], sl_files[3])
        self.rollout_classifier = Classifier(rollout_files[0], rollout_files[1], rollout_files[2], rollout_files[3])
        self.value_function = Classifier(value_files[0], value_files[1], value_files[2], value_files[3], True)

    def re_root(self, state):
        if (self.root == None):
            print "Created initial MCTS"
            self.root = GameStateNode(state, self.sl_classifier, 0)
        elif (state.to_tuple() in self.root.children_gamestates):
            print "Found gamestate"
            self.root = self.root.children_gamestates[state.to_tuple()]
        else:
            print "Created new gamestate"
            self.root = GameStateNode(state, self.sl_classifier, self.root.turn_num + 1)

    def select_add_actionpair(self):
        current = self.root

        # Take the actions with the maximum UCT score
        my_action = max(current.my_actions, key=lambda i: current.my_actions[i])
        opp_action = max(current.opp_actions, key=lambda i: current.opp_actions[i])
        key = (my_action, opp_action)

        # Iteratively traverse the tree until we find an action pair which has
        # not been added to the tree
        while (key in current.children_actionpairs):
            if current.state.is_over():
                break
            actionpair_node = current.children_actionpairs[key]

            # TODO: 0 for now, change when non-deterministic
            current = actionpair_node.children_gamestates[0]


            my_action = max(current.my_actions, key=lambda i: current.my_actions[i])
            opp_action = max(current.opp_actions, key=lambda i: current.opp_actions[i])
            key = (my_action, opp_action)

        # Create a new action pair node and add it to the tree
        new_actionpair = ActionPairNode(current, key)
        current.children_actionpairs[key] = new_actionpair

        # Return the new action pair
        return new_actionpair

    def add_gamestate(self, actionpair_node, new_state): 
        new_gamestate = GameStateNode(new_state, self.sl_classifier, actionpair_node.parent.turn_num + 1, actionpair_node)
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
            for a in node.my_actions:
                node.update_uct_scores((a, None))
            for b in node.opp_actions:
                node.update_uct_scores((None, b))

    def best_move(self):
        best_action = max(self.root.my_actions, key=lambda i: self.root.my_actions_n[i][0] / self.root.my_actions_n[i][1])
        opp_action = max(self.root.opp_actions, key=lambda i: self.root.opp_actions_n[i][0] / self.root.opp_actions_n[i][1])
        return best_action, 0.0, opp_action



class Node(object):
    def __init__(self, parent=None):
        self.times_visited = 0.0
        self.wins = 0.0
        self.parent = parent

    def increment(self, outcome):
        self.times_visited += 1
        self.wins += outcome


class GameStateNode(Node):
    def __init__(self, state, sl_classifier, turn_num, parent=None):
        super(GameStateNode, self).__init__(parent)

        self.state = state

        self.turn_num = turn_num

        self.my_legal_actions_probs = state.get_legal_actions_probs(sl_classifier, turn_num, 0)
        self.opp_legal_actions_probs = state.get_legal_actions_probs(sl_classifier, turn_num, 1)

        # Wins and number of times visited for all actions
        # {action : [wins, num_visited]}
        self.my_actions_n = {a: [0.0, 1.0] for a in self.my_legal_actions_probs[0]}
        self.opp_actions_n = {b: [0.0, 1.0] for b in self.opp_legal_actions_probs[0]}

        # print "Num my actions:", len(self.my_legal_actions_probs[0])
        # print "Num opp actions:", len(self.opp_legal_actions_probs[0])

        # Probabilities for each action
        self.my_actions_p = dict(zip(self.my_legal_actions_probs[0], self.my_legal_actions_probs[1]*len(self.my_legal_actions_probs[0])))
        self.opp_actions_p = dict(zip(self.opp_legal_actions_probs[0], self.opp_legal_actions_probs[1]*len(self.opp_legal_actions_probs[0])))

        # Our and our opponent's actions
        # {action : uct_score}
        # Initially the same my/opp_actions_p
        self.my_actions = deepcopy(self.my_actions_p)
        self.opp_actions = deepcopy(self.opp_actions_p)

        # Our (immediate) action pair children
        # {(my_action, opp_action) : action pair node}
        self.children_actionpairs = {}

        # Our gamestate children (one level below)
        # {(game_state_tuple) : game_state_node}
        self.children_gamestates = {}
        if parent is not None:
            self.parent.parent.children_gamestates[state.to_tuple()] = self


    def increment(self, outcome, action_pair):
        self.times_visited += 1
        self.wins += outcome
        self.my_actions_n[action_pair[0]][0] += outcome
        self.opp_actions_n[action_pair[1]][0] += 1 - outcome
        self.my_actions_n[action_pair[0]][1] += 1
        self.opp_actions_n[action_pair[1]][1] += 1

    def update_uct_scores(self, action_pair):
        C = 0.5

        my_action = action_pair[0]
        opp_action = action_pair[1]
        
        if my_action:
            my_n = self.my_actions_n[my_action][1]
            my_mean = self.my_actions_n[my_action][0] / my_n
            my_explore = 2 * C * np.sqrt(2 * np.log(self.times_visited) / my_n)
            my_prob = self.my_actions_p[my_action]
            self.my_actions[my_action] = my_mean + my_prob/my_n

        if opp_action:
            opp_n = self.opp_actions_n[opp_action][1]
            opp_mean = self.opp_actions_n[opp_action][0] / opp_n
            opp_explore = 2 * C * np.sqrt(2 * np.log(self.times_visited) / opp_n)
            opp_prob = self.opp_actions_p[opp_action]
            self.opp_actions[opp_action] = opp_mean + opp_prob/opp_n


class ActionPairNode(Node):
    def __init__(self, parent, action_pair):
        super(ActionPairNode, self).__init__(parent)

        self.action_pair = action_pair
        self.children_gamestates = []
