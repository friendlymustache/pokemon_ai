import pandas
import numpy as np
import xgboost
import time
from sklearn import cross_validation
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from scipy import io
from scipy import sparse as sp
from sklearn.cross_validation import train_test_split
import sys
import pickle

def label_encoder_filename(model_name):
    return "%s_label_encoder.pickle"%model_name    

def classifier_filename(model_name):
    return "%s.bst"%model_name

def load_label_encoder(model_name):
    f = open(label_encoder_filename(model_name))
    result = pickle.load(f)
    f.close()
    return result

def train_helper(X_train, X_test, y_train, y_test, model_name):
    xg_train = xgboost.DMatrix( X_train, label=y_train)
    xg_test = xgboost.DMatrix(X_test, label=y_test)

    le = load_label_encoder(model_name)

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
    print "Training classifier..."
    t1 = time.time()
    bst = xgboost.train(param, xg_train, 500, evals, early_stopping_rounds=10)
    xgboost.plot_importance(bst)
    t2 = time.time()
    print t2-t1
    bst.save_model(classifier_filename(model_name))
    return bst

def read_matrices(X_filename, Y_filename, model_name):
    le = LabelEncoder()

    # Load labels of training data
    y_csv = pandas.read_csv(Y_filename, index_col=0)
    Y = y_csv.values.ravel()

    # Encode training data labels and save encoder
    Y = le.fit_transform(Y)
    pickle_file = open(label_encoder_filename(model_name), "w")    
    pickle.dump(le, pickle_file)
    pickle_file.close()

    # Load training data
    X = sp.csr_matrix(io.mmread(X_filename))
    print "Matrix info for model %s:"%model_name
    print X.shape, Y.shape, len(le.classes_) 

    return (X, Y)    



def train_classifier(X_filename, Y_filename, model_name):
    X, Y = read_matrices(X_filename, Y_filename, model_name)
    # Split training data into train/eval sets 
    indices = range(len(Y))
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(X, Y, indices, test_size=0.33)

    # Train classifier on train set using eval set to measure validation
    # error, saving trained classifier to disk
    bst = train_helper(X_train, X_test, y_train, y_test, model_name)

    # Return the indices of the training/test set
    return (idx_train, idx_test, bst)



def main():
    if len(sys.argv) < 4:
        print "usage: python model_xgb.py <X_fname> <switch_vs_all_fname> <moves_vs_all_fname>"
        print "X_fname: Filename (mtx format) of non-label portion of training data"
        print "switch_vs_all_fname: Filename (csv) of labels for switch vs all classification"
        print "moves_vs_all_fname: Filename (csv) of labels for moves vs all classification"        
        return

    X_fname = sys.argv[1]
    switch_vs_all_fname = sys.argv[2]
    moves_vs_all_fname = sys.argv[3]

    # Get row indices of training and eval data of switch vs all classifier,
    # use same rows as training and eval set of moves vs all classifier
    switch_model_name = "switch_vs_all"
    idx_train, idx_test, switch_vs_all_clf = train_classifier(X_fname, switch_vs_all_fname, switch_model_name)

    # Get matrices for moves vs all classifier, passing in model name
    # to use for saving the label encoder
    moves_model_name = "moves_vs_all"
    moves_X, moves_Y = read_matrices(X_fname, moves_vs_all_fname, moves_model_name)

    X_train = moves_X[idx_train]
    y_train = moves_Y[idx_train]
    X_test = moves_X[idx_test]
    y_test = moves_Y[idx_test]

    # Done splitting train/eval sets for moves data, so delete
    # moves data from RAM
    del moves_X
    del moves_Y

    # Train moves vs all classifier
    moves_vs_all_clf = train_helper(X_train, X_test, y_train, y_test, moves_model_name)

    # Done training classifiers, so we can delete training sets from RAM
    del X_train
    del y_train

    # Use classifiers + eval sets to compute error
    test_data = xgboost.DMatrix(X_test)
    switch_predictions = switch_vs_all_clf.predict(test_data, ntree_limit=switch_vs_all_clf.best_ntree_limit)
    moves_predictions = moves_vs_all_clf.predict(test_data, ntree_limit=moves_vs_all_clf.best_ntree_limit)


    eval_set_size = len(y_test)
    num_correct = 0.0
    num_switches_correct = 0.0

    # NOTE: We might not actually check the prediction of our moves
    # model for all training points, so evaluate error on the ones
    # we actually predict (we predict on moves only when we
    # correctly predict that there is no switch)
    num_moves_correct = 0.0
    num_moves_predicted = 0.0

    # Evaluate 0-1 error of combined model

    # Load test set of switch vs all
    switch_X, switch_Y = read_matrices(X_fname, switch_vs_all_fname, switch_model_name)
    switch_test = switch_Y[idx_test]

    del switch_X
    del switch_Y

    # Load label encoder of switch predictor
    switch_le = load_label_encoder(switch_model_name)

    for i in xrange(eval_set_size):
        # Check switch predictions
        probs = switch_predictions[i]
        model_prediction = np.argmax(probs)
        actual_label = switch_test[i]

        # If switch prediction was incorrect, we have an incorrect prediction
        # so continue
        if model_prediction != actual_label:
            continue

        num_switches_correct += 1

        # If we correctly predicted a switch, add to correct predictions
        # and continue
        if model_prediction != switch_le.transform(str(-1)): 
            num_correct += 1
            continue

        # If we correctly predicted that we're going to use one of our
        # current poke's moves instead of switching, check that the move
        # prediction was correct
        probs = moves_predictions[i]
        model_prediction = np.argmax(probs)
        actual_label = y_test[i]

        assert(type(model_prediction) == type(actual_label))

        num_moves_predicted += 1
        if model_prediction == actual_label:
            num_correct += 1
            num_moves_correct += 1



    print "Fraction correct: (%s / %s): %s"%(num_correct, eval_set_size, num_correct / eval_set_size)
    print "Switches correct: (%s / %s): %s"%(num_switches_correct, eval_set_size, num_switches_correct / eval_set_size)
    print "Moves correct: (%s / %s): %s"%(num_moves_correct, num_moves_predicted, num_moves_correct / num_moves_predicted)

    # Count the number of times elements of switch_test aren't equal to
    # the hardcoded token for a non-switch (-1)
    num_switches = np.count_nonzero(switch_test != switch_le.transform("-1"))

    print "Fraction of switches in dataset: %s"%(float(num_switches) / eval_set_size)




if __name__ == "__main__":
    main()


