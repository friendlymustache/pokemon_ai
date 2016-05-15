import pandas
import numpy
import xgboost
import time
from sklearn import cross_validation
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

# Converts categorical to integers
le = LabelEncoder()

# Load Data
data = pandas.read_csv('data.csv')
data.fillna(0, inplace=True)
names = list(data)
Y = data[names[-1]]
data.drop([names[-1]], axis=1, inplace=True)

# Convert categorical columns to integers
cats = []
for i in range(len(names)-1):
    if data[names[i]].dtype != 'int64' and data[names[i]].dtype != 'float64':
        data[names[i]] = le.fit_transform(data[names[i]])
        cats.append(i)
data = data.values

# One hot encode data
encoder = OneHotEncoder(categorical_features=numpy.array(cats))
new_data = encoder.fit_transform(data)
print new_data.shape

# Train XGBoost
print "Training"
t1 = time.time()
clf = xgboost.XGBClassifier(n_estimators=1,max_depth=3,learning_rate=0.03, objective="multi:softmax")
scores = cross_validation.cross_val_score(clf, new_data, Y, scoring='accuracy', cv=2, n_jobs=-1) 
print(scores.mean())
t2 = time.time()
print t2-t1