import pandas as pd
import pickle
from sklearn import preprocessing
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from global_constants import dataset_name, model_filename

def target_names(code: int) -> str:
    uncode = {0:"common", 1:"spam", 2:"minor", 3:"help"}
    return uncode[code]

dataset = pd.read_csv(dataset_name, ";")

y = pd.factorize(dataset['response'])[0]
x = dataset.drop('response', axis=1)

train_x, test_x, train_y, test_y = train_test_split(x,y, test_size=0.2, random_state=42, stratify=y)

scale = preprocessing.StandardScaler().fit(train_x)

pipeline = make_pipeline(preprocessing.StandardScaler(),RandomForestClassifier(n_estimators=100))
hyperparameters = { 'randomforestclassifier__max_features' : ['auto', 'sqrt', 'log2'],'randomforestclassifier__max_depth': [None, 5, 3, 1]}

RF_model = GridSearchCV(pipeline, hyperparameters, cv=10)
RF_model.fit(train_x,train_y)

pred_y = RF_model.predict(test_x)
print("MSE: ",mean_squared_error(test_y,pred_y))
print("Accuracy: ",RF_model.score(test_x,test_y))
"""pickle.dump(RF_model, open(model_filename,'wb'))"""