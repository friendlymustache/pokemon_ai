"""
Parses the HTML representing a given replay's
sequence of moves/events into a graph of move co-occurrences.
"""
import pandas
import re
import json
# Add parent directory to module search path
import sys
import os
sys.path.append(os.path.abspath("../"))



from path import path
from database import ReplayDatabase
from showdownai.log import SimulatorLog
from showdownai.data import NAME_CORRECTIONS, MOVE_CORRECTIONS, load_data, get_move, correct_name, get_hidden_power
from showdownai.move_predict import create_predictor
from showdownai.team import Team, Pokemon
from showdownai.simulator import Simulator
from showdownai.feature_encoders import GamestateEncoder
from smogon import SmogonMoveset
from showdownai.gamestate import GameState
from compiler.ast import flatten
import scipy.sparse as sp
from scipy import io
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import pickler
import time

DENSE_DATA_LINE_LENGTH = 118
SPARSE_DATA_LINE_LENGTH = 1964
RESULT_LOC = "../data/sl_data/"

from datetime import datetime


pokedata = None
smogon_data = None
smogon_bw_data = None
simulator = None

dense_data = []
sparse_data = []
Y = []
poke_names = set()

class InvalidDataFormat(Exception):
    pass


def get_poke_info(name):
    '''
    Returns a Pokemon instance (see team.py for class definition) 
    corresponding to the pokemon with the specified name
    '''
    poke_name = correct_name(name)
    if poke_name in smogon_data:
        moveset = [m for m in smogon_data[poke_name].movesets if 'Overused' == m['tag'] or 'Underused' == m['tag'] or 'Rarelyused' == m['tag'] or 'Neverused' == m['tag'] or 'Unreleased' == m['tag'] or 'Ubers' == m['tag'] or 'PU' in m['tag']]
        if len(moveset) > 1:
            moveset = SmogonMoveset.from_dict(moveset[1])
        elif len(moveset) == 1:
            moveset = SmogonMoveset.from_dict(moveset[0])
        else:
            moveset = [m for m in smogon_bw_data[poke_name].movesets if 'Overused' == m['tag'] or 'Underused' == m['tag'] or 'Rarelyused' == m['tag'] or 'Neverused' == m['tag'] or 'Unreleased' == m['tag'] or 'Ubers' == m['tag'] or 'PU' in m['tag']]
            moveset = SmogonMoveset.from_dict(moveset[0])
    elif poke_name not in smogon_data and poke_name in smogon_bw_data:
        moveset = [m for m in smogon_bw_data[poke_name].movesets if 'Overused' == m['tag'] or 'Underused' == m['tag'] or 'Rarelyused' == m['tag'] or 'Neverused' == m['tag'] or 'Unreleased' == m['tag'] or 'Ubers' == m['tag'] or 'PU' in m['tag']]
        moveset = SmogonMoveset.from_dict(moveset[0])
    else:
        moveset = SmogonMoveset(None, None, None, {'hp': 88, 'patk': 84, 'pdef': 84, 'spatk': 84, 'spdef': 84, 'spe': 84}, {'hp': 1.0, 'patk': 1.0, 'pdef': 1.0, 'spatk': 1.0, 'spdef': 1.0, 'spe': 1.0}, None, 'ou')
    moveset.moves = None
    if poke_name in smogon_data:
        typing = smogon_data[poke_name].typing
        stats = smogon_data[poke_name].stats
    elif poke_name not in smogon_data and poke_name in smogon_bw_data:
        typing = smogon_bw_data[poke_name].typing
        stats = smogon_bw_data[poke_name].stats
    else:
        typing = ['Normal']
        stats = {'hp': 80, 'patk': 80, 'pdef': 80, 'spatk': 80, 'spdef': 80, 'spe': 80}
    predictor = create_predictor('PokeFrequencyPredictor', name, pokedata)
    poke = Pokemon(name, typing, stats, moveset, predictor, calculate=True)
    moves = [x[0] for x in poke.predict_moves([])]
    poke.moveset.moves = moves[:4]
    poke.health = poke.final_stats['hp']
    poke.alive = True 
    return poke   


def parse_poke_names(poke_names):
    result = []
    for name in poke_names:
        if name is not None:
            result.append(get_poke_info(name))
    return result

def create_initial_gamestate(first_turn_lines):
    log = SimulatorLog()
    log.add_events(first_turn_lines)

    for event in log.events:
        if event.type == "battle_started":
            p1_username = event.details['username']
            p2_username = event.details['username1']

    my_poke_list = []
    my_poke_names = []
    opp_poke_names = []

    for event in log.events:
        if event.type == "team":
            if event.details['username'] == p1_username:
                my_poke_names = event.details['team']
            else:
                opp_poke_names = event.details['team']

    my_poke_list = parse_poke_names(my_poke_names)
    opp_poke_list = parse_poke_names(opp_poke_names)


    # Construct objects to represent our team + the opponent's team
    my_pokes = Team(my_poke_list)
    opp_pokes = Team(opp_poke_list)
    teams = [my_pokes, opp_pokes]

    # Get all events corresponding to pokemon switches, use these
    # to determine each player's initial pokemon
    switches = filter(lambda event: event.type == "switch", log.events)
    assert(len(switches) == 2)
    for event in switches:
        # Get the team object corresponding to the current player
        team = teams[event.player]
        team.primary_poke = team.get_poke_index(event.poke)

    return GameState(teams)

def update_latest_turn(gamestate, turn, turn_num=0, encoder=None):
    simulator.latest_turn = []
    for line in turn:
        event = simulator.log.add_event(line)
        if not event:
            continue
        simulator.latest_turn.append(event)
        if event.type == "move":
            dense_line_data, sparse_line_data = gamestate.to_list(encoder=encoder)
            dense_line_data.append(turn_num)
            dense_line_data.append(event.player)
            if 'Struggle' in dense_line_data or 'Struggle' in event.details['move']:
                return False

            # Use when doing switches vs all classification
            # Y.append(-1)
            Y.append(event.details['move'])     

            # TODO uncomment to build + save dense data           
            dense_data.append(dense_line_data)
            sparse_data.append(sparse_line_data)

            if len(dense_line_data) != DENSE_DATA_LINE_LENGTH:
                raise InvalidDataFormat("Line length: %s, expected: %s. Sparse data length: %s"%(len(dense_line_data), DENSE_DATA_LINE_LENGTH, len(sparse_line_data)))
            elif sparse_line_data.shape[1] != SPARSE_DATA_LINE_LENGTH:
                raise InvalidDataFormat("Line length: %s, expected: %s. Dense data length: %s"%(sparse_line_data.shape[1], SPARSE_DATA_LINE_LENGTH, len(dense_line_data)))                

        elif event.type == "switch":
            dense_line_data, sparse_line_data = gamestate.to_list(encoder=encoder)
            dense_line_data.append(turn_num)
            dense_line_data.append(event.player)

            if 'Struggle' in dense_line_data:
                return False

            # Use when doing moves vs all classification
            # Y.append(-1)

            # Use the index of the pokemon being switched-to
            # with respect to its corresponding team object (
            # curr_player_team = gamestate.teams[event.player]
            # Y.append(curr_player_team.get_poke_index(event.poke))
            Y.append(event.poke)


            # TODO uncomment to build + save dense data
            dense_data.append(dense_line_data)
            sparse_data.append(sparse_line_data)

            if len(dense_line_data) != DENSE_DATA_LINE_LENGTH:
                raise InvalidDataFormat("Line length: %s, expected: %s. Sparse data length: %s"%(len(dense_line_data), DENSE_DATA_LINE_LENGTH, sparse_line_data.shape[1]))
            elif sparse_line_data.shape[1] != SPARSE_DATA_LINE_LENGTH:
                raise InvalidDataFormat("Line length: %s, expected: %s. Dense data length: %s"%(sparse_line_data.shape[1], SPARSE_DATA_LINE_LENGTH, len(dense_line_data)))                            
           
        simulator.handle_event(gamestate, event)
    return gamestate

def parse_lines(lines, encoder=None):
    turns = []
    buff = []
    for line in lines:
        if re.match(r"Turn [0-9]+", line):
            turns.append(buff)
            buff = []
        else:
            buff.append(line)
    turns.append(buff)
    gamestate = create_initial_gamestate(turns[0])
    gamestate = update_latest_turn(gamestate, turns[0], encoder=encoder)
    for i in range(1, len(turns)):
        gamestate = update_latest_turn(gamestate, turns[i], turn_num=i, encoder=encoder)
        if not gamestate:
            break


if __name__ == "__main__":
    start = time.time()
    if len(sys.argv) != 2:
        print "usage: python log_parser.py <prefix>"
        print "<prefix> is used as a filename prefix for the files generated by the parser"
        sys.exit(1)

    print "=== Running log parser, expecting feature vectors of length " \
     "%s ==="%(SPARSE_DATA_LINE_LENGTH + DENSE_DATA_LINE_LENGTH)
    print "NOTE: Generated files will be in %s"%RESULT_LOC

    if not os.path.exists(RESULT_LOC):
        os.makedirs(RESULT_LOC)            

    # Connects to SQLite database stored in file at ../data/db
    db = ReplayDatabase()
    pokedata = load_data('../data')
    smogon_data = pokedata.smogon_data
    smogon_bw_data = pokedata.smogon_bw_data
    successes = 0.0
    failures = 0.0
    encoder = GamestateEncoder()    
    # For each replay (battle log)...
    for idx, log_attributes in enumerate(db.get_replay_attributes("battle_log", "username", "replay_id")):
            simulator = Simulator(pokedata)
            log, user, replay_id = log_attributes
            try:
                lines = log.split('\n')
                parse_lines(lines, encoder=encoder)
                successes += 1
            except InvalidDataFormat as e:
                raise e
            except (Exception) as e:            
                failures += 1
                print e

            if idx % 100 == 0:
                sys.stderr.write("Successes: %s, failures: %s, percent success: %s\n"%(successes, failures, successes / (successes + failures)))
    sys.stderr.write("Successes: %s, failures: %s, percent success: %s\n"%(successes, failures, successes / (successes + failures)))

    # Combine all sparse data into one sparse matrix
    sparse_data = sp.vstack(sparse_data)
    dense_data = pandas.DataFrame(dense_data)

    # Converts categorical to integers
    dense_data.fillna(0, inplace=True)
    names = list(dense_data)

    # Convert categorical columns to integers, saving list of 
    # resulting label encoders to a file
    cats = []
    label_encoders = []
    for i in range(len(names)):
        if dense_data[names[i]].dtype != 'int64' and dense_data[names[i]].dtype != 'float64':
            le = LabelEncoder()
            dense_data[names[i]] = le.fit_transform(dense_data[names[i]])
            label_encoders.append(le)
            cats.append(i)
    dense_data = dense_data.values

    # Save label encoders to disk
    path_prefix = "%s/%s"%(RESULT_LOC, sys.argv[1])
    pickler.dump_object(label_encoders, "%s_X_encoders.pickle"%path_prefix)

    # Label-encode our supervised training examples' labels (Y) and save the
    # encoder
    y_encoder = LabelEncoder()
    Y = y_encoder.fit_transform(Y)
    pickler.dump_object(y_encoder, "%s_Y_encoder.pickle"%path_prefix)

    # Save labels
    moves = pandas.DataFrame(Y)
    moves.to_csv("%s_labels.csv"%path_prefix)

    # Save feature vectors (unlabeled portion of training data)
    dense_data = sp.hstack((dense_data, sparse_data))
    sys.stderr.write("%s\n"%str(dense_data.shape))
    data_filename = "%s_features.csv"%(path_prefix)
    io.mmwrite(data_filename, dense_data)

    end = time.time()
    print "Done parsing, took %s sec"%(end - start)