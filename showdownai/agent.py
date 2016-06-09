from simulator import Simulator, Action
from monte_carlo import MonteCarloTree

import logging
import time
import numpy
import random

logging.basicConfig()

class Agent():

    def get_action(self, gamestate, who):
        raise NotImplementedError()

class HumanAgent(Agent):

    def get_action(self, gamestate, who):
        valid = False
        my_team = gamestate.get_team(who)
        print "My moves:", [m for m in my_team.primary().moveset.moves]
        print "My switches:", [(m, i) for i, m in enumerate(my_team.poke_list) if m != my_team.primary() and m.alive]
        my_legal = gamestate.get_legal_actions(who, log=True)
        while not valid:
            action_string = raw_input('> ')
            try:
                my_action = Action.create(action_string)
                if my_action not in my_legal:
                    print "Illegal move", my_action, my_legal
                    assert False
                valid = True
            except:
                pass
        return my_action

class MinimaxAgent(Agent):

    def __init__(self, depth, pokedata, use_cache=True, alphabet=True, log_file=None):
        self.depth = depth
        self.simulator = Simulator(pokedata)
        self.cache = {}
        self.hit_count = 0
        self.prune_count = 0
        self.use_cache = use_cache
        self.alphabet = alphabet
        self.log_file = log_file

    def get_action(self, state, who, log=True):
        start = time.time()
        best_action, value, opp_action = self.minimax(state, self.depth, who, log=log)
        end = time.time()
        elapsed = end - start
        if self.log_file is not None:
            with open(self.log_file, 'a') as fp:
                print >>fp, elapsed
        if best_action:
            if best_action.is_move():
                my_move_name = state.get_team(who).primary().moveset.moves[best_action.move_index]
            if opp_action.is_move():
                opp_move_name = state.get_team(1 - who).primary().moveset.moves[opp_action.move_index]
            if best_action.is_switch():
                my_move_name = "Switch[%s]" % state.get_team(who).poke_list[best_action.switch_index]
            if opp_action.is_switch():
                opp_move_name = "Switch[%s]" % state.get_team(1 - who).poke_list[opp_action.switch_index]
            if log:
                print "I think you are going to use %s(%s, %s, %s) and I will use %s(%s, %s, %s)." % (
                    opp_move_name, opp_action.backup_switch, opp_action.mega, opp_action.volt_turn,
                    my_move_name, best_action.backup_switch, best_action.mega, best_action.volt_turn,
                )
        return best_action

class PessimisticMinimaxAgent(MinimaxAgent):

    def minimax(self, state, depth, who, log=False):
        if state.is_over() or depth == 0:
            return None, state.evaluate(who), None
        my_legal_actions = state.get_legal_actions(who)
        opp_legal_actions = state.get_legal_actions(1 - who)
        my_v = float('-inf')
        best_action = None
        best_best_opp_action = None
        actions = [None, None]
        for my_action in my_legal_actions:
            opp_v = float("inf")
            best_opp_action = None
            actions[who] = my_action
            for opp_action in opp_legal_actions:
                actions[1 - who] = opp_action
                new_state = self.simulator.simulate(state, actions, who)
                tuple_state = new_state.to_tuple()
                if self.use_cache and (depth, tuple_state) in self.cache:
                    new_action, state_value = self.cache[(depth, tuple_state)]
                    self.hit_count += 1
                else:
                    new_action, state_value, _ = self.minimax(new_state, depth - 1, who)
                    self.cache[(depth, tuple_state)] = (my_action, state_value)
                if opp_v >= state_value:
                    opp_v = state_value
                    best_opp_action = opp_action
                if self.alphabet and state_value < my_v:
                    self.prune_count += 1
                    break
            if opp_v > my_v:
                best_action = my_action
                best_best_opp_action = best_opp_action
                my_v = opp_v
        return best_action, my_v, best_best_opp_action

class OptimisticMinimaxAgent(MinimaxAgent):

    def minimax(self, state, depth, who, log=False):
        if state.is_over() or depth == 0:
            return None, state.evaluate(who), None
        my_legal_actions = state.get_legal_actions(who)
        opp_legal_actions = state.get_legal_actions(1 - who)
        opp_v = float('inf')
        best_action = None
        best_best_my_action = None
        actions = [None, None]
        for opp_action in opp_legal_actions:
            my_v = float("-inf")
            best_my_action = None
            actions[1 - who] = opp_action
            for my_action in my_legal_actions:
                actions[who] = my_action
                new_state = self.simulator.simulate(state, actions, who)
                tuple_state = new_state.to_tuple()
                if (depth, tuple_state) in self.cache:
                    new_action, state_value = self.cache[(depth, tuple_state)]
                    self.hit_count += 1
                else:
                    new_action, state_value, _ = self.minimax(new_state, depth - 1, who)
                    self.cache[(depth, tuple_state)] = (my_action, state_value)
                if my_v < state_value:
                    my_v = state_value
                    best_my_action = my_action
                if state_value > opp_v:
                    self.prune_count += 1
                    break
            if my_v < opp_v:
                best_action = opp_action
                best_best_my_action = best_my_action
                opp_v = my_v
        return best_best_my_action, opp_v, best_action


class MonteCarloAgent(Agent):
    def __init__(self, maxtime, pokedata, sl_policy=None):
        self.lmbda = 0.5
 
        sl_model_file = 'models/sl/sl_simple.bst'
        sl_feature_labels_file = 'models/sl/sl_X_encoders.pickle'
        sl_cats_file = 'models/sl/sl_cats.pickle'
        sl_target_label_file = 'models/sl/sl_Y_encoder.pickle'
        sl_files = [sl_model_file, sl_feature_labels_file, sl_cats_file, sl_target_label_file]
 
        rollout_model_file = 'models/sl/sl_simple.bst'
        rollout_files = [rollout_model_file, sl_feature_labels_file, sl_cats_file, sl_target_label_file]
 
        value_model_file = 'models/value/value_func.bst'
        value_feature_labels_file = 'models/value/value_func_X_encoders.pickle'
        value_cats_file = 'models/value/value_func_cats.pickle'
        value_target_label_file = 'models/value/value_func_Y_encoder.pickle'
        value_files = [value_model_file, value_feature_labels_file, value_cats_file, value_target_label_file]
 
        self.maxtime = maxtime
        self.simulator = Simulator(pokedata)
        self.tree = MonteCarloTree(sl_files, rollout_files, value_files)
        self.sl_policy = sl_policy
        print "Monte Carlo tree created"

    def get_action(self, state, who, log=True):
        print "Getting action"
        start = time.time()
        best_action, value, opp_action = self.search(state, who, start, log=log)

        '''if best_action:
            if best_action.is_move():
                my_move_name = state.get_team(who).primary().moveset.known_moves[best_action.move_index]
            if opp_action.is_move():
                opp_move_name = state.get_team(1 - who).primary().moveset.moves[opp_action.move_index]
            if best_action.is_switch():
                my_move_name = "Switch[%s]" % state.get_team(who).poke_list[best_action.switch_index]
            if opp_action.is_switch():
                opp_move_name = "Switch[%s]" % state.get_team(1 - who).poke_list[opp_action.switch_index]
            if log:
                print "I think you are going to use %s(%s, %s, %s) and I will use %s(%s, %s, %s)." % (
                    opp_move_name, opp_action.backup_switch, opp_action.mega, opp_action.volt_turn,
                    my_move_name, best_action.backup_switch, best_action.mega, best_action.volt_turn,
                )'''

        return best_action

    def rollout(self, state, turn_num):
        winner = state.get_winner()
 
        while not winner:
            my_action_probs = state.get_legal_actions_probs(self.tree.rollout_classifier, turn_num, 0, probs=False)
            opp_action_probs = state.get_legal_actions_probs(self.tree.rollout_classifier, turn_num, 1, probs=False)
            my_action = numpy.random.choice(my_action_probs[0], p=my_action_probs[1])
            opp_action = numpy.random.choice(opp_action_probs[0], p=opp_action_probs[1])
            state = self.simulator.simulate(state, (my_action, opp_action), 0, add_action=True)
            winner = state.get_winner()
            turn_num += 1
 
        return int(winner == 1)

    def search(self, state, who, start, log=False):
        self.tree.re_root(state)
        count = 0

        while (time.time() - start) < self.maxtime:
            # select an action pair and get new actionpair node
            child = self.tree.select_add_actionpair()

            # run simulation given previous state and action chosen, return new state
            parent_state = child.parent.state.deep_copy()
            winner = parent_state.get_winner()
            if winner != 0:
                outcome = int(winner==1)
                self.tree.back_propogate(child.parent, outcome)
            else:
                new_state = self.simulator.simulate(parent_state, child.action_pair, who, add_action=True)
                
                # add new gamestate node to tree
                leaf = self.tree.add_gamestate(child, new_state)
                
                # run rollout policy and backpropogate outcome
                num_times = 1
                outcome = 0.0
                for i in range(num_times):
                    outcome += self.rollout(new_state.deep_copy(), child.parent.turn_num + 1)
                outcome /= num_times

                outcome = (1-self.lmbda)*outcome + self.lmbda*new_state.value_function(self.tree.value_function, child.parent.turn_num + 1, 0)
                self.tree.back_propogate(leaf, outcome)
            count += 1

        print "Searched", count, "Nodes"
        return self.tree.best_move()
