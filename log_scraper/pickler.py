'''
Module for interfacing with pickle (dumping/loading objects to/from disk)
'''

import pickle

def dump_object(obj, filename):
    '''
    Saves a pickled version of the passed-in object using
    the specified filename
    '''
    f = open(filename, "w")
    pickle.dump(obj, f)
    f.close()

def load_object(filename):
    f = open(filename)
    obj = pickle.load(f)
    f.close()
    return obj