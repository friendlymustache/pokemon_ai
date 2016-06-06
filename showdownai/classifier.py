import xgboost
import pickle
from all_pokes_and_moves import ALL_POKEMON, ALL_MOVES

class Classifier():

    def __init__(self, model_file, feature_labels_file, target_label_file, cats_file):
        self.xgb = xgboost.Booster(model_file=model_file)
        self.feature_label_encoders = pickle.load(open(feature_labels_file, 'rb'))
        self.target_label_encoder = pickle.load(open(target_label_file, 'rb'))
        self.cat_indices = pickle.load(open(cats_file, 'rb'))

        self.pokemon_names = list(set(ALL_POKEMON).intersection(self.target_label_encoder.classes_)) 
        self.pokemon_indices = self.target_label_encoder.transform(self.pokemon_names)
        self.pokemon_dict = dict(zip(self.pokemon_names, self.pokemon_indices))
        self.move_names = list(set(ALL_MOVES).intersection(self.target_label_encoder.classes_)) 
        self.move_indices = self.target_label_encoder.transform(self.move_names)
        self.move_dict = dict(zip(self.move_names, self.move_indices))
        
    def predict(self, encoded_list):
        xg_data = xgboost.DMatrix(encoded_list)
        return self.xgb.predict(xg_data)