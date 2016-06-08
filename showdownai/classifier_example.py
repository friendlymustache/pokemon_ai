import pickle
from scipy import io
from scipy.sparse import csr_matrix
import numpy
from classifier import Classifier

c = Classifier('../data/sl_data/value_func_model.bst', '../data/sl_data/value_func_X_encoders.pickle', '../data/sl_data/value_func_cats.pickle', '../data/sl_data/value_func_Y_encoder.pickle', value_function=True)
X = io.mmread('../data/sl_data/value_func_features.csv.mtx')
X = X.tocsc()
print c.predict(X[0:50, :])
if c.value_function:
    print numpy.round(c.predict(X[0:50, :]))
else:
    print c.target_label_encoder.inverse_transform(numpy.argmax(c.predict(X[0:50, :]), axis=1))