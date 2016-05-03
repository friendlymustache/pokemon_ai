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


directory = path('.')
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
    '''
    Validates a line of a battle log. Currently, just checks if line
    describes the tier of the battle, and if so, checks that the tier
    is OU
    '''
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
        f.write(json.dumps(poke_graph, sort_keys=True,indent=4, separators=(',', ': ')))
