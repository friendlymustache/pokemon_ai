"""
Parses the HTML representing a given replay's
sequence of moves/events into a graph of move co-occurrences.
TODO: parse logs into a feature representation
of each game state
"""

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


'''directory = path('.')
USER_PLAYER = r"\|player\|(?P<player>.+?)\|(?P<username>.+?)\|.*?"
POKE = r"\|poke\|p(?P<player>.+?)\|(?P<poke>.+)"
SWITCH = r"\|switch\|p(?P<player>.+?)a: (?P<nickname>.+?)\|(?P<pokename>.+)\|.+?"
DRAG = r"\|drag\|p(?P<player>.+?)a: (?P<nickname>.+?)\|(?P<pokename>.+)\|.+?"
MOVE = r"\|move\|p(?P<player>.+?)a: (?P<poke>.+?)\|(?P<move>.+?)\|.+?"
MOVE_CORRECTIONS = {"ExtremeSpeed": "Extreme Speed",
                    "ThunderPunch": "Thunder Punch",
                    "SolarBeam": "Solar Beam",
                    "DynamicPunch": "Dynamic Punch"}
TIER =  r"\|tier\|(?P<tier>.+)"

def handle_line(username, line):
    line = line.strip()
    # If line is invalid for some reason, return False
    # so that we can stop processing the current battle log
    if not validate_line(line):
        return False

    match = re.match(USER_PLAYER, line)
    if match:
        if match.group("player") == "p1" and match.group("username").lower() != username.lower():
            global player
            player = "1"
        elif match.group("player") == "p2" and match.group("username").lower() != username.lower():
            global player
            player = "2"
    match = re.match(POKE, line)
    if match:
        if player == match.group("player"):
            poke = match.group("poke").split(",")[0]
            # Filter out item information
            poke = poke.split("|")[0]
            if poke == "Zoroark":
                return False
            elif poke == "Zorua":
                return False
            elif "Keldeo" in poke:
                poke = "Keldeo"
            opp_team[poke] = []
    match = re.match(SWITCH, line)
    if match:
        if player == match.group("player"):
            nickname = match.group("nickname")
            pokename = match.group("pokename").split(",")[0]
            if "-Mega" in pokename:
                pokename = pokename[:-5]
            if pokename == "Charizard-M":
                pokename = "Charizard"
            if "Gourgeist" in pokename:
                for name in opp_team:
                    if "Gourgeist" in name:
                        gourgeist = name
                opp_team[pokename] = opp_team[gourgeist]
            if "Keldeo" in pokename:
                pokename = "Keldeo"
            if "Keldeo" in nickname:
                nickname = "Keldeo"
            opp_nicknames[nickname] = pokename
    match = re.match(DRAG, line)
    if match:
        if player == match.group("player"):
            nickname = match.group("nickname")
            pokename = match.group("pokename").split(",")[0]
            if "-Mega" in pokename:
                pokename = pokename[:-5]
            if pokename == "Charizard-M":
                pokename = "Charizard"
            if "Keldeo" in pokename:
                pokename = "Keldeo"
            if "Keldeo" in nickname:
                nickname = "Keldeo"
            opp_nicknames[nickname] = pokename
    match = re.match(MOVE, line)
    if match:
        poke = match.group("poke")
        if "Keldeo" in poke:
            poke = "Keldeo"
        if player == match.group("player"):
            # if poke not in opp_nicknames:
            #     print "%s not in %s"%(poke, opp_nicknames)
            # if opp_nicknames[poke] not in opp_team:
            #     print "%s not in %s"%(opp_nicknames[poke], opp_team)

            if match.group("move") not in opp_team[opp_nicknames[poke]]:
                opp_team[opp_nicknames[poke]].append(match.group("move"))
    return True

def validate_line(line):
    #Validates a line of a battle log. Currently, just checks if line
    #describes the tier of the battle, and if so, checks that the tier
    #is OU
    return validate_tier(line)

def validate_tier(line):
    tier_match = re.match(TIER, line)    
    # Return False current line gives us information on the tier of the
    # current game and the tier is not OU. Otherwise, return True. 
    if tier_match and tier_match.group("tier") != "OU":
        return False
    return True




def make_graph_move(opp_team, graph_move, graph_move_frequencies):
    for poke in opp_team:
        for move in opp_team[poke]:
            if move in MOVE_CORRECTIONS:
                move = MOVE_CORRECTIONS[move]
            if move not in graph_move_frequencies:
                graph_move_frequencies[move] = 0
            if move not in graph_move:
                graph_move[move] = {}
            graph_move_frequencies[move] += 1
            for othermove in opp_team[poke]:
                if othermove in MOVE_CORRECTIONS:
                    othermove = MOVE_CORRECTIONS[othermove]
                if move == othermove:
                    continue
                if othermove in graph_move[move]:
                    graph_move[move][othermove] += 1
                else:
                    graph_move[move][othermove] = 1
    return graph_move, graph_move_frequencies


def make_graph_poke(opp_team, graph_poke, graph_frequencies):
    for poke in opp_team:
        if poke not in graph_poke:
            graph_poke[poke] = {}
        if poke not in graph_frequencies:
            graph_frequencies[poke] = {}
        for move in opp_team[poke]:
            if move in MOVE_CORRECTIONS:
                move = MOVE_CORRECTIONS[move]
            if move not in graph_poke[poke]:
                graph_poke[poke][move] = {}
            if move not in graph_frequencies[poke]:
                graph_frequencies[poke][move] = 0
            graph_frequencies[poke][move] += 1
            for othermove in opp_team[poke]:
                if othermove in MOVE_CORRECTIONS:
                    othermove = MOVE_CORRECTIONS[othermove]
                if move == othermove:
                    continue
                if othermove in graph_poke[poke][move]:
                    graph_poke[poke][move][othermove] += 1
                else:
                    graph_poke[poke][move][othermove] = 1
    return graph_poke, graph_frequencies

class Zoroark(Exception):
    pass

if __name__ == "__main__":
    graph_poke = {}
    graph_move = {}
    graph_move_frequencies = {}
    graph_frequencies = {}
    # Connects to SQLite database stored in file at ../data/db
    db = ReplayDatabase()

    # For each replay (battle log)...
    for idx, log_attributes in enumerate(db.get_replay_attributes("battle_log", "username")):
            log, user = log_attributes
            print "Parsing log %s"%idx
            player = ""
            opp_team = {}
            opp_nicknames = {}
            lines = log.split("\n")
            valid_line = True
            # Parse each line of the log
            for line in lines:
                # If we were unable to parse the current line,
                # we're parsing an invalid battle log, so skip the remainder
                # of its lines
                valid_line = handle_line(user, line)
                if not valid_line:
                    break
            if valid_line:
                graph_poke, graph_move_frequencies = make_graph_poke(opp_team, graph_poke, graph_move_frequencies)
    poke_graph = {
        'frequencies': graph_move_frequencies,
        'cooccurences': graph_poke,
    }
    with open("graph_move.json", "w") as f:
        f.write(json.dumps(poke_graph, sort_keys=True,indent=4, separators=(',', ': ')))'''
    

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
    print("Updating with latest information...")
    #old_gamestate = gamestate
    #gamestate = gamestate.deep_copy()
    #simulator.append_log(gamestate, turn)
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
    # I don't know what this does...
    '''move_events = []
    for event in simulator.latest_turn:
        if event.type == "move":
            move_events.append(event)
    if len(move_events) == 2 and move_events[0].player == 1:
        my_move = move_events[1].details['move']
        opp_move = move_events[0].details['move']
        if my_move == "Hidden Power":
            my_move = get_hidden_power(move_events[1].poke, smogon_data)
        if opp_move == "Hidden Power":
            opp_move = get_hidden_power(move_events[0].poke, smogon_data)
        if my_move in MOVE_CORRECTIONS:
            my_move = MOVE_CORRECTIONS[my_move]
        if opp_move in MOVE_CORRECTIONS:
            opp_move = MOVE_CORRECTIONS[opp_move]
        my_move = get_move(my_move)
        opp_move = get_move(opp_move)
        if move_events[0].player != simulator.get_first(old_gamestate, [my_move, opp_move], 0):
            opp_poke = old_gamestate.get_team(1).primary()
            for poke in gamestate.get_team(1).poke_list:
                if poke.name == opp_poke.name:
                    poke.item = "Choice Scarf"'''
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
    '''for idx, log_attributes in enumerate(db.get_replay_attributes("battle_log", "username")):
            log, user = log_attributes
            print log
            #log = log.encode('utf-8')
            lines = log.split('\n')
            parse_lines(lines)
            break'''
    # Example usage
    lines = [line.rstrip('\n') for line in open('example_log.txt', 'rb')]
    parse_lines(lines)
    for line in data:
        print line