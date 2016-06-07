import pickle
from scipy import io
from scipy.sparse import csr_matrix
import numpy
from classifier import Classifier

c = Classifier('../data/sl_data/two_tree.bst', '../data/sl_data/first_run_X_encoders.pickle', '../data/sl_data/first_run_cats.pickle', '../data/sl_data/first_run_Y_encoder.pickle', value_function=False)
X = io.mmread('../data/sl_data/first_run_features.csv.mtx')
X = X.tocsc()
print c.predict(X[0:10, :])
if c.value_function:
    print numpy.round(c.predict(X[0:10, :]))
else:
    print c.target_label_encoder.inverse_transform(numpy.argmax(c.predict(X[0:10, :]), axis=1))