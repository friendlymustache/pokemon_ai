import pandas
import numpy
import xgboost
import time
import sys
import os
import pickler
from sklearn import cross_validation
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from scipy import io
from sklearn.cross_validation import train_test_split
from datetime import datetime
from log_parser import RESULT_LOC as PARSER_RESULT_LOC

def main(prefix, result_fname): 

    path_prefix = os.path.join(PARSER_RESULT_LOC, prefix)

    X_fname = "%s_features.csv.mtx"%(path_prefix)
    Y_fname = "%s_labels.csv"%(path_prefix)
    result_fname = "%s/%s"

    moves = pandas.read_csv(Y_fname, index_col=0)
    Y = moves.values.ravel()
    X = io.mmread(X_fname)
    num_classes = len(set(Y))
    print X.shape, Y.shape, num_classes

    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.33)

    xg_train = xgboost.DMatrix( X_train, label=y_train)
    xg_test = xgboost.DMatrix(X_test, label=y_test)

    param = {}
    # use softmax multi-class classification
    param['objective'] = 'multi:softprob'
    param['eval_metric'] = 'merror'

    # use binary logistic classification with a default error function
    # (used for value function)
    # param['objective'] = 'binary:logistic'    

    param['eta'] = 0.001
    param['max_depth'] = 7
    param['nthread'] = 36
    param['num_class'] = len(set(Y))

    evals = [ (xg_train, 'train'), (xg_test, 'eval') ]

    # Train xgboost
    print "Training"
    t1 = time.time()
    bst = xgboost.train(param, xg_train, 500, evals, early_stopping_rounds=10)
    t2 = time.time()
    print t2-t1

    if result_fname is None:
        result_fname = str(datetime.now())

    bst.save_model("%s.bst"%result_fname)

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "usage: python model_xgb.py prefix result_fname"
        print "prefix: Prefix of training data files/encoder files " \
            "(argument used when running log_parser.py)"
        # print "X_fname: Filename (mtx format) of non-label portion of training data"
        # print "Y_fname: Filename (csv) of labels for training data"
        print "result_fname: Filename at which to store trained model"       
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])