"""
Parses the HTML representing a given replay's
sequence of moves/events into a graph of move co-occurrences.
TODO: parse logs into a feature representation
of each game state
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
import cPickle


username = None
username1 = None
pokedata = None
smogon_data = None
smogon_bw_data = None
simulator = None

dense_data = []
sparse_data = []
Y = []
poke_names = set()

def create_initial_gamestate(turn_0):
    log = SimulatorLog()
    for line in turn_0:
        log.add_event(line)
    for event in log.events:
        if event.type == "battle_started":
            username = event.details['username']
            username1 = event.details['username1']

    my_poke_list = []
    my_poke_names = []
    opp_poke_names = []
    for event in log.events:
        if event.type == "team":
            if event.details['username'] == username:
                my_poke_names = event.details['team']
            else:
                opp_poke_names = event.details['team']

    for name in my_poke_names:
        if not name:
            continue
        poke_name = correct_name(name)
        "Corrected to:", poke_name
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
        my_poke_list.append(poke)

    opp_poke_list = []
    for name in opp_poke_names:
        if not name:
            continue
        poke_name = correct_name(name)
        "Corrected to:", poke_name
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
        opp_poke_list.append(poke)

    my_primary = None
    opp_primary = None
    for event in log.events:
        if event.type == "switch" and event.player == 0:
            for poke in my_poke_list:
                if poke.name == event.poke:
                    my_primary = my_poke_list.index(poke)
        elif event.type == "switch" and event.player == 1:
            for poke in opp_poke_list:
                if poke.name == event.poke:
                    opp_primary = opp_poke_list.index(poke)
    assert my_primary != None
    my_pokes = Team(my_poke_list)
    opp_pokes = Team(opp_poke_list)
    my_pokes.primary_poke = my_primary
    opp_pokes.primary_poke = opp_primary

    gamestate = GameState([my_pokes, opp_pokes])
    return gamestate

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
            dense_line_data.append(event.details['move'])
            if 'Struggle' in dense_line_data or 'Struggle' in event.details['move']:
                return False
            Y.append(event.details['move'])                
            dense_data.append(dense_line_data)
            sparse_data.append(sparse_line_data)

        elif event.type == "switch":
            dense_line_data, sparse_line_data = gamestate.to_list(encoder=encoder)
            dense_line_data.append(turn_num)
            dense_line_data.append(event.player)
            dense_line_data.append(event.poke)

            if 'Struggle' in dense_line_data:
                return False
            Y.append(event.poke)                
            dense_data.append(dense_line_data)
            sparse_data.append(sparse_line_data)
           
        simulator.handle_event(gamestate, event)
    return gamestate

def parse_lines(lines, encoder=None):
    turns = []
    buffer = []
    for line in lines:
        if re.match(r"Turn [0-9]+", line):
            turns.append(buffer)
            buffer = []
        else:
            buffer.append(line)
    turns.append(buffer)
    gamestate = create_initial_gamestate(turns[0])
    gamestate = update_latest_turn(gamestate, turns[0], encoder=encoder)
    for i in range(1, len(turns)):
        print "TURN", i
        gamestate = update_latest_turn(gamestate, turns[i], turn_num=i, encoder=encoder)
        if not gamestate:
            break

if __name__ == "__main__":
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
            # except Exception as e:
            #     failures += 1
            # Catches acceptable errors
            # except (AttributeError, KeyError, AssertionError, ValueError) as e:
            except (Exception) as e:            
                failures += 1
                print e
            # Catches unacceptable errors and prints the replay id + game log of the
            # offending replay
            # except ValueError:
            #     sys.stderr.write(replay_id)
            #     sys.stderr.write("\n\n\n\n\n")
            #     sys.stderr.write(log)
            if idx % 100 == 0:
                sys.stderr.write("Successes: %s, failures: %s, percent success: %s\n"%(successes, failures, successes / (successes + failures)))
    sys.stderr.write("Successes: %s, failures: %s, percent success: %s\n"%(successes, failures, successes / (successes + failures)))
    print "Poke names: %s"%poke_names
    print "%s pokemon names in parsed data"%(len(poke_names))

    # Combine all sparse data into one sparse matrix
    sparse_data = sp.vstack(sparse_data)
    dense_data = pandas.DataFrame(dense_data)

    # Converts categorical to integers
    le = LabelEncoder()
    dense_data.fillna(0, inplace=True)
    names = list(dense_data)

    # Convert categorical columns to integers
    cats = []
    for i in range(len(names)):
        if dense_data[names[i]].dtype != 'int64' and dense_data[names[i]].dtype != 'float64':
            dense_data[names[i]] = le.fit_transform(dense_data[names[i]])
            cats.append(i)
    dense_data = dense_data.values

    moves = pandas.DataFrame(Y)
    moves.to_csv("moves.csv")

    dense_data = sp.hstack((dense_data, sparse_data))
    sys.stderr.write(str(dense_data.shape))
    io.mmwrite("data_low_dim.csv", dense_data)

    # dense_data.to_csv("data.csv", index=False)