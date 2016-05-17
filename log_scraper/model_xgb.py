import pandas
import numpy
import xgboost
import time
from sklearn import cross_validation
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from scipy import io
from sklearn.cross_validation import train_test_split
import joblib

le = LabelEncoder()
moves = pandas.read_csv('moves.csv', index_col=0)
Y = moves.values.ravel()
Y = le.fit_transform(Y)
X = io.mmread("data_low_dim.csv")
print X.shape, Y.shape, len(le.classes_) 

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.33)

xg_train = xgboost.DMatrix( X_train, label=y_train)
xg_test = xgboost.DMatrix(X_test, label=y_test)

param = {}
# use softmax multi-class classification
param['objective'] = 'multi:softprob'
param['eta'] = 0.002
param['max_depth'] = 7
param['nthread'] = 7
param['num_class'] = len(le.classes_)
param['eval_metric'] = 'merror'
evals = [ (xg_train, 'train'), (xg_test, 'eval') ]

# Train xgboost
print "Training"
t1 = time.time()
bst = xgboost.train(param, xg_train, 500, evals, early_stopping_rounds=3)
t2 = time.time()
print t2-t1
bst.save_model('clf.p')