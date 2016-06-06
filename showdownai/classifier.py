import xgboost
import pickle

class Classifier():

    def __init__(self, model_file, feature_labels_file, target_label_file, cats_file):
        self.xgb = xgboost.Booster(model_file=model_file)
        self.feature_label_encoders = pickle.load(open(feature_labels_file, 'rb'))
        self.target_label_encoder = pickle.load(open(target_label_file, 'rb'))
        self.cat_indices = pickle.load(open(cats_file, 'rb'))
        
    def predict(self, encoded_list):
        xg_data = xgboost.DMatrix(encoded_list)
        return self.xgb.predict(xg_data)