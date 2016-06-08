import pickle
from simulator import Action
from type import get_multiplier
from data import MOVES
import logging
import sys
from compiler.ast import flatten
from feature_encoders import GamestateEncoder
import numpy
import scipy.sparse as sp
import random
logging.basicConfig()

class GameState():
    def __init__(self, teams):
        self.teams = teams
        self.rocks = [False, False]
        self.spikes = [0, 0]

    def dump(self, path):
        with open(path, 'wb') as fp:
            pickle.dump(self, fp)

    @staticmethod
    def load(path):
        with open(path, 'rb') as fp:
            gs = pickle.load(fp)
        return gs

    def deep_copy(self):
        state = GameState([x.copy() for x in self.teams])
        state.rocks = self.rocks[:]
        state.spikes = self.spikes[:]
        return state

    def set_rocks(self, who, rock_bool):
        self.rocks[who] = rock_bool

    def add_spikes(self, who):
        self.spikes[who] += 1

    def get_team(self, team):
        return self.teams[team]

    def validate_teams(self):
        return len(self.teams[0].poke_list) == 6 and len(self.teams[1].poke_list) == 6
    
    def to_encoded_list(self, label_encoders, cats, turn_num, player_num):
        dense_data, sparse_data = self.to_list()
        dense_data = [0 if elm is None else elm for elm in dense_data]
        dense_data.append(turn_num)
        dense_data.append(player_num)
        for i in range(len(cats)):
            try:
                dense_data[cats[i]] = label_encoders[i].transform([dense_data[cats[i]]])[0]
            except:
                dense_data[cats[i]] = 0
        return sp.hstack((dense_data, sparse_data))

    def to_list(self, encoder=None):

        if encoder==None:
            encoder = GamestateEncoder()
        
        if not self.validate_teams():
            return False

        first_team_dense, first_team_sparse = self.teams[0].to_list(encoder=encoder)
        second_team_dense, second_team_sparse = self.teams[1].to_list(encoder=encoder)
        additional_state = [self.rocks[0], self.rocks[1], self.spikes[0], self.spikes[1]]
        dense_data = [first_team_dense, second_team_dense, additional_state]

        return (flatten(dense_data), sp.hstack([first_team_sparse, second_team_sparse]))


    def to_tuple(self):
        return (tuple(x.to_tuple() for x in self.teams), (self.rocks[0], self.rocks[1], self.spikes[0], self.spikes[1]))

    @staticmethod
    def from_tuple(tupl):
        return GameState([team.from_tuple() for team in tupl[0]])

    def value_function(self, classifier, turn_num, player_num):
        prob = classifier.predict(self.to_encoded_list(classifier.feature_label_encoders, classifier.cat_indices, turn_num, player_num))[0]
        if player_num == 0:
            prob = 1.0-prob
        return prob

    def evaluate(self, who):
        win_bonus = 0
        my_team = self.get_team(who)
        opp_team = self.get_team(1 - who)
        if self.is_over():
            if my_team.alive():
                win_bonus = 10000
            else:
                win_bonus = -10000
        my_team_health = sum([x.health/x.final_stats['hp'] for x in my_team.poke_list])
        opp_team_health = sum([x.health/x.final_stats['hp'] for x in opp_team.poke_list])
        my_team_death = len([x for x in my_team.poke_list if not x.alive])
        opp_team_death = len([x for x in opp_team.poke_list if not x.alive])
        my_burn, opp_burn = 0, 0
        my_rocks, opp_rocks = 0, 0
        spikes = 0
        if self.is_over():
            my_team_stages, opp_team_stages = 0, 0
        else:
            my_poke = my_team.primary()
            opp_poke = opp_team.primary()
            my_team_stages = my_poke.stages['spatk'] + my_poke.stages['patk']
            opp_team_stages = opp_poke.stages['spatk'] + opp_poke.stages['patk']
            opp_rocks = 0.75 if self.rocks[1 - who] else 0
            my_rocks = -1.0 if self.rocks[who] else 0
            if self.spikes[1 - who] == 1:
                spikes = 0.3
            elif self.spikes[1 - who] == 2:
                spikes = 0.6
            elif self.spikes[1 - who] == 3:
                spikes = 1
            opp_burn = 0.75 if (opp_poke.status == "burn" and opp_poke.final_stats['patk'] > 245 and opp_poke.ability != "Guts") else 0
            my_burn = -1.5 if (my_poke.status == "burn" and my_poke.final_stats['patk'] > 250 and my_poke.ability != "Guts") else 0
        return win_bonus + my_team_health - opp_team_health - 0.5 * my_team_death + 0.5 * opp_team_death + opp_rocks + my_rocks + opp_burn + my_burn + spikes# + 0.07 * (my_team_stages - opp_team_stages)

    def is_over(self):
        return not (self.teams[0].alive() and self.teams[1].alive())
    
    def get_winner(self):
        if not self.is_over():
            return 0
        if self.teams[0].alive():
            return 1
        else:
            return 2

    def switch_pokemon(self, switch_index, who, log=False, hazards=True):
        my_team = self.get_team(who)
        opp_team = self.get_team(1 - who)
        if my_team.primary().name == "Meloetta":
            my_team.primary().meloetta_reset()
        my_team.set_primary(switch_index)
        my_poke = my_team.primary()
        my_poke.reset_taunt()
        my_poke.reset_disabled()
	my_poke.reset_last_move()
	my_poke.reset_encore()
        opp_poke = opp_team.primary()
        if log:
            pass
            # print (
            #     "%s switched in." % my_poke
            # )
        if my_poke.ability == "Intimidate":
            if log:
                pass
                # print ("%s got intimidated." % opp_poke)
            opp_poke.decrease_stage('patk', 1)
        if self.rocks[who] and hazards:
            type = 1.0
            type_multipliers = [get_multiplier(x, "Rock") for x in my_poke.typing]
            for x in type_multipliers:
                type *= x
            damage = 1.0 / 8 * type
            d = my_poke.damage_percent(damage)
            if log:
                pass
                # print "%s was damaged %f due to rocks!" % (my_poke, d)
            if self.spikes[who] > 0 and "Flying" not in my_poke.typing and my_poke.ability != "Levitate":
                if self.spikes[who] == 1:
                    d = my_poke.damage_percent(1.0 / 8)
                elif self.spikes[who] == 2:
                    d = my_poke.damage_percent(1.0 / 6)
                elif self.spikes[who] == 3:
                    d = my_poke.damage_percent(1.0 / 4)
                if log:
                    pass
                    # print "%s was damaged %f due to spikes!" % (my_poke, d)


    def get_legal_actions_probs(self, classifier, turn_num, player_num, log=False):
        my_team = self.get_team(player_num)
        my_poke = my_team.primary()
        opp_team = self.get_team(1 - player_num)
        opp_poke = opp_team.primary()
        mega = my_poke.can_evolve()

        pokemon = range(len(my_team.poke_list))
        valid_switches = [i for i in pokemon if my_team.poke_list[i].alive and i != my_team.primary_poke]
        valid_backup_switches = valid_switches + [my_team.primary_poke]
        if len(valid_switches) == 0:
            valid_switches = [None]

        move_names = []
        move_probs = []
        classifier_probs = classifier.predict(self.to_encoded_list(classifier.feature_label_encoders, classifier.cat_indices, turn_num, player_num))[0, :]
        if my_poke.choiced:
            move_names = [my_poke.move_choice]
            move_probs = numpy.ones(1)
        elif len(my_poke.moveset.known_moves) < 4:
            move_names = classifier.move_names
            move_probs = classifier_probs[classifier.move_indices]
        else:
            move_names = my_poke.moveset.known_moves
            my_move_indices = numpy.array([classifier.move_dict[move] for move in move_names if move in classifier.move_dict])
            move_probs = classifier_probs[my_move_indices]

        move_probs = numpy.repeat(move_probs, len(valid_switches))
        moves = []
        for i in range(len(move_names)):
            move_name = move_names[i]
            if move_name in my_poke.moveset.known_moves:
                move_index = my_poke.moveset.known_moves.index(move_name)
            else:
                move_index = -1
            if move_name == "U-turn" or move_name == "Volt Switch":
                if valid_switches[0] == None:
                    moves.append(
                        Action(
                            "move",
                            move_index=move_index,
                            mega=mega,
                            volt_turn=None,
                            backup_switch=None
                        )
                    )
                else:
                    switches = valid_backup_switches[:]
                    for a in xrange(1, len(switches)):
                            b = random.choice(xrange(0, a))
                            switches[a], switches[b] = switches[b], switches[a]
                    moves.extend([
                        Action("move", move_index=move_index, mega=mega, volt_turn=valid_switches[j], backup_switch=switches[j], move_name=move_name)
                        for j in range(len(valid_switches))
                    ])
            else:
                moves.extend([
                    Action("move", move_index=move_index, mega=mega, backup_switch=j, move_name=move_name)
                    for j in valid_switches
                ])

        if valid_switches == [None]:
            switch_probs = []
        else:
            switch_indices = numpy.array([classifier.pokemon_dict[my_team.poke_list[i].name] for i in valid_switches])
            switch_probs = numpy.repeat(classifier_probs[switch_indices], len(valid_backup_switches)-1)
        switches = [Action("switch", switch_index=i, backup_switch=j) for i in valid_switches for j in valid_backup_switches if j != i and i is not None]

        if opp_poke.ability == "Magnet Pull" and "Steel" in my_poke.typing and "Ghost" not in my_poke.typing:
            switches = []
            switch_probs = []
        elif opp_poke.ability == "Shadow Tag" and "Ghost" not in my_poke.typing:
            switches = []
            switch_probs = []
        elif opp_poke.ability == "Arena Trap" and "Ghost" not in my_poke.typing and "Flying" not in my_poke.typing:
            switches = []
        if my_poke.taunt:
            moves = [move for move in moves if MOVES[my_poke.moveset.moves[move.move_index]].category != "Non-Damaging"]
            indices = numpy.array([i for i in range(len(moves)) if MOVES[my_poke.moveset.moves[moves[i].move_index]].category != "Non-Damaging"])
            move_probs = move_probs[indices]
        if my_poke.disabled is not None:
            moves = [move for move in moves if my_poke.moveset.moves[move.move_index] != my_poke.disabled]
            indices = [i for i in range(len(moves)) if my_poke.moveset.moves[moves[i].move_index] != my_poke.disabled]
            move_probs = move_probs[indices]
        if my_poke.encore:
            moves = [move for move in moves if my_poke.moveset.moves[move.move_index] == my_poke.last_move]
            indices = [i for i in range(len(moves)) if my_poke.moveset.moves[moves[i].move_index] == my_poke.last_move]

        total = moves+switches
        total_probs = numpy.hstack((move_probs, switch_probs))
        total_probs /= numpy.sum(total_probs)
        return (total, total_probs)

    def get_legal_actions(self, who, log=False):
        my_team = self.get_team(who)
        my_poke = my_team.primary()
        opp_team= self.get_team(1 - who)
        opp_poke = opp_team.primary()

        pokemon = range(len(my_team.poke_list))
        valid_switches = [i for i in pokemon if my_team.poke_list[i].alive and i != my_team.primary_poke]
        valid_backup_switches = valid_switches + [my_team.primary_poke]
        if len(valid_switches) == 0:
            valid_switches = [None]


        moves = []
        switches = []
        for move_index in range(len(my_poke.moveset.moves)):
            move_name = my_poke.moveset.moves[move_index]
            mega = my_poke.can_evolve()
            if my_poke.choiced:
                if move_name != my_poke.move_choice:
                    continue
            if move_name == "U-turn" or move_name == "Volt Switch":
                for j in valid_switches:
                    for k in valid_backup_switches:
                        if j == None:
                            moves.append(
                                Action(
                                    "move",
                                    move_index=move_index,
                                    mega=mega,
                                    volt_turn=j,
                                    backup_switch=None
                                )
                            )
                        elif j != None and k != None and j != k:
                            moves.append(
                                Action(
                                    "move",
                                    move_index=move_index,
                                    volt_turn=j,
                                    backup_switch=k,
                                    mega=mega
                                )
                            )
            else:
                moves.extend([
                    Action("move", move_index=move_index, mega=mega, backup_switch=j)
                    for j in valid_switches
                ])
        switches.extend([Action("switch", switch_index=i, backup_switch=j) for i in valid_switches for j in valid_backup_switches if j != i and i is not None])

        if opp_poke.ability == "Magnet Pull" and "Steel" in my_poke.typing and "Ghost" not in my_poke.typing:
            switches = []
        elif opp_poke.ability == "Shadow Tag" and "Ghost" not in my_poke.typing:
            switches = []
        elif opp_poke.ability == "Arena Trap" and "Ghost" not in my_poke.typing and "Flying" not in my_poke.typing:
            switches = []
        if my_poke.taunt:
            moves = [move for move in moves if MOVES[my_poke.moveset.moves[move.move_index]].category != "Non-Damaging"]
        if my_poke.disabled is not None:
            moves = [move for move in moves if my_poke.moveset.moves[move.move_index] != my_poke.disabled]
	if my_poke.encore:
            moves = [move for move in moves if my_poke.moveset.moves[move.move_index] == my_poke.last_move]
	    

        return moves + switches
