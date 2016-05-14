"""
Parses the HTML representing a given replay's
sequence of moves/events into a graph of move co-occurrences.
TODO: parse logs into a feature representation
of each game state
"""
import pandas
import re
import json
from path import path
from database import ReplayDatabase
from showdownai.log import SimulatorLog
from showdownai.data import NAME_CORRECTIONS, MOVE_CORRECTIONS, load_data, get_move, correct_name, get_hidden_power
from showdownai.move_predict import create_predictor
from showdownai.team import Team, Pokemon
from showdownai.simulator import Simulator
from smogon import SmogonMoveset
from showdownai.gamestate import GameState
from compiler.ast import flatten

username = None
username1 = None
pokedata = None
smogon_data = None
smogon_bw_data = None
simulator = None

data = []

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

def update_latest_turn(gamestate, turn, turn_num=0):
    simulator.latest_turn = []
    for line in turn:
        event = simulator.log.add_event(line)
        if not event:
            continue
        simulator.latest_turn.append(event)
        if event.type == "move":
            data_line = gamestate.to_list()
            data_line.append(turn_num)
            data_line.append(event.player)
            data_line.append(event.details['move'])
            data.append(data_line)
        elif event.type == "switch":
            data_line = gamestate.to_list()
            data_line.append(turn_num)
            data_line.append(event.player)
            data_line.append(event.poke)
            data.append(data_line)
        simulator.handle_event(gamestate, event)
    return gamestate

def parse_lines(lines):
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
    gamestate = update_latest_turn(gamestate, turns[0])
    for i in range(1, len(turns)):
        print "TURN", i
        update_latest_turn(gamestate, turns[i], turn_num=i)

if __name__ == "__main__":
    # Connects to SQLite database stored in file at ../data/db
    db = ReplayDatabase()
    pokedata = load_data('../data')
    smogon_data = pokedata.smogon_data
    smogon_bw_data = pokedata.smogon_bw_data
    simulator = Simulator(pokedata)
    # For each replay (battle log)...
    for idx, log_attributes in enumerate(db.get_replay_attributes("battle_log", "username")):
            log, user = log_attributes
            lines = log.split('\n')
            try:
                parse_lines(lines)
            except KeyError as e:
                print e

    df = pandas.DataFrame(data)
    print df.shape
    df.to_csv("data.csv", index=False)