'''
Contains classes used to one-hot encode team and moveset
information
'''
import sys
import os
sys.path.append(os.path.abspath("../"))

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
        return self.moves_map[move_name]

    def sanitize_move(self, move_name):
        if "Hidden Power" in move_name:
            return "Hidden Power"
        return move_name

    def encode_list_helper(self, dictionary, lst, index=False):
        # Get the non-zero indices of the output
        lst_indices = [dictionary[elem] if elem in dictionary else 0 for elem in lst]
        result = [0] * len(dictionary)        
        for i in range(len(lst_indices)):
            if index:
                result[lst_indices[i]] = i
            else:
                result[lst_indices[i]] = 1
        return result

    def encode_team(self, poke_names):
        '''
        One-hot encode a team
        '''
        return self.encode_list_helper(self.pokemon_map, poke_names, index=True)

    def encode_moveset(self, moveset):
        '''
        One-hot encode a moveset
        '''
        processed_moveset = map(self.sanitize_move, moveset)
        return self.encode_list_helper(self.moves_map, processed_moveset)


if __name__ == "__main__":
    encoder = GamestateEncoder()

