'''
Contains classes used to one-hot encode team and moveset
information
'''
import sys
import os
sys.path.append(os.abspath("../"))

# from smogon.smogon import Smogon

from all_pokes_and_moves import ALL_POKEMON, ALL_MOVES

class GamestateEncoder:
    def __init__(self):
        self.pokemon_map = self.idx_to_name_dict(ALL_POKEMON)
        self.moves_map = self.idx_to_name_dict(ALL_MOVES)        
        
    def idx_to_name_dict(self, array):
        dictionary = {}
        for idx, val in enumerate(array):
            dictionary[val] = idx
        assert(len(dictionary) == len(array))   
        return dictionary

    def encode_poke_name(self, poke_name):
        return self.pokemon_map[poke_name]     

    def encode_move(self, move_name):
        return self.move_map[move_name]

    def encode_list_helper(self, dictionary, lst):
        # Get the non-zero indices of the output
        lst_indices = [dictionary[elem] for elem in lst]
        result = [0] * len(dictionary)
        for idx in lst_indices:
            result[idx] = 1
        return result


    def encode_team(self, poke_names):
        '''
        One-hot encode a team
        '''
        return self.encode_list_helper(self.pokemon_map, poke_names)

    def encode_moveset(self, moveset):
        '''
        One-hot encode a moveset
        '''
        processed_moveset = map(self.sanitize_move, moveset)
        return self.encode_list_helper(self.moves_map, processed_moveset)


if __name__ == "__main__":
    encoder = GamestateEncoder()

