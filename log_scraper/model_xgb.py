import pandas
import numpy
import xgboost
import time
import sys
from sklearn import cross_validation
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from scipy import io
from sklearn.cross_validation import train_test_split
from datetime import datetime

def main(X_fname, Y_fname, result_fname=None): 
    le = LabelEncoder()
    moves = pandas.read_csv(Y_fname, index_col=0)
    Y = moves.values.ravel()
    Y = le.fit_transform(Y)
    X = io.mmread(X_fname)
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

    if result_fname is None:
        result_fname = str(datetime.now())

    bst.save_model("%s.bst"%result_fname)

if __name__ == "__main__":

    if len(sys.argv) < 4:
        print "usage: python model_xgb.py prefix [result_fname]"
        print "X_fname: Filename (mtx format) of non-label portion of training data"
        print "Y_fname: Filename (csv) of labels for training data"
        print "result_fname: Filename at which to store trained model " \
            "(defaults to current datetime) "        
        sys.exit(1)

    X_fname = sys.argv[1]
    Y_fname = sys.argv[2]
    result_fname = sys.argv[3]
    main(X_fname, Y_fname, result_fname)