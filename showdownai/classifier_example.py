import pickle
from scipy import io
from scipy.sparse import csr_matrix
import numpy
from classifier import Classifier

c = Classifier('../data/sl_data/two_tree.bst', '../data/sl_data/first_run_X_encoders.pickle', '../data/sl_data/first_run_cats.pickle', target_label_file='../data/sl_data/first_run_Y_encoder.pickle')
X = io.mmread('../data/sl_data/first_run_features.csv.mtx')
X = X.tocsc()
print c.predict(X[0:10, :])
print c.target_label_encoder.inverse_transform(numpy.argmax(c.predict(X[0:10, :]), axis=1))