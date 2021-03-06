# -*- coding: utf-8 -*-
"""DY_Random_Forest.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NVJwOmbnRYkfXtArAEHTfKrpJHNUCSQw
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import numpy as np
import sklearn.metrics as metrics
import math
from sklearn.tree import export_graphviz
import pydot
from sklearn.model_selection import cross_val_score, KFold
from sklearn.inspection import permutation_importance
from sklearn.model_selection import RandomizedSearchCV# Number of trees in random forest

directory = "D:/My Drive/Data 270 project/Data"
df = pd.read_csv(directory + "/NORMALIZED_TABLE.csv") #will put the normalized combined table into a dataframe
df

#sets the independent variables
X = df.iloc[:, 1:26]

#sets the prediction targets/
y = df.iloc[:,-1]

#split the data in testing and remaining dataset
X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.2, random_state = 42)
print("X_train shape:",X_train.shape)
print("y_train shape:",y_train.shape)
print("X_test shape:",X_test.shape)
print("y_test shape:",y_test.shape)

training_data = [X_train, y_train]
training_subset = pd.concat(training_data, axis=1, join='inner')
training_subset

testing_data = [X_test, y_test]
testing_subset = pd.concat(testing_data, axis=1, join='inner')
testing_subset

"""### hyperparameter tuning"""

n_estimators = [int(x) for x in np.linspace(start = 200, stop = 2000, num = 10)]
# Number of features to consider at every split
max_features = ['auto', 'sqrt']
# Maximum number of levels in tree
max_depth = [int(x) for x in np.linspace(10, 110, num = 11)]
max_depth.append(None)
# Minimum number of samples required to split a node
min_samples_split = [2, 5, 10]
# Minimum number of samples required at each leaf node
min_samples_leaf = [1, 2, 4]
# Method of selecting samples for training each tree
bootstrap = [True, False]# Create the random grid
random_grid = {'n_estimators': n_estimators,
               'max_features': max_features,
               'max_depth': max_depth,
               'min_samples_split': min_samples_split,
               'min_samples_leaf': min_samples_leaf,
               'bootstrap': bootstrap}

# Use the random grid to search for best hyperparameters
# First create the base model to tune
rf = RandomForestRegressor()
# Random search of parameters, using 3 fold cross validation, 
# search across 100 different combinations, and use all available cores
rf_random = RandomizedSearchCV(estimator = rf, param_distributions = random_grid, n_iter = 100, cv = 3, verbose=2, random_state=42, n_jobs = -1)# Fit the random search model
rf_random.fit(X_train, y_train)
rf_random.best_params_

"""### testing"""

rf = RandomForestRegressor(n_estimators = 1400, max_depth = 100, min_samples_split = 2,min_samples_leaf = 1,max_features = 'auto',bootstrap = True, random_state = 42)
rf.fit(X_train, y_train)
kfold = KFold(n_splits = 10, shuffle = True)
cv_scores = cross_val_score(rf, X_train, y_train, cv=kfold)

y_pred_test=rf.predict(X_test)
#finding absolute error for validation
errors_test = abs(y_pred_test - y_test)

#root mean square error and mean square error
mse_test = metrics.mean_squared_error(y_test, y_pred_test)
rmse_test = math.sqrt(mse_test)

#r2 score
r2_test = rf.score(X_test, y_test)

print("Training R2 Score:", round(rf.score(X_train, y_train),5))
print('Testing R2 Score:', round(r2_test,5))
print("Average KFold Cross Validation score:", round(cv_scores.mean(),5))
print('Mean Absolute Error:', round(np.mean(errors_test), 5))
print('Mean Square Error:', round(mse_test,5))
print('Root Mean Square Error:', round(rmse_test,5))

# adjusted R2
adj_r2_test = 1 - (1-r2_test)*(len(y_test)-1)/(len(y_test)-X_test.shape[1]-1)
print('The adjusted r2 score is:', round(adj_r2_test,5))

Test = pd.DataFrame({'Actual-Values': np.array(y_test).flatten(), 'Predicted-Values': y_pred_test.flatten()})

Test

x_plane = range(len(y_test))
plt.figure(figsize=(15, 10))
plt.scatter(x_plane, y_test, c = 'green', label = 'Actual-values')
plt.plot(x_plane, y_pred_test, label = 'Predicted-Values')
plt.title("Reservoir Actual vs Predicted Values")
plt.xlabel('Records')
plt.ylabel('Normalized Reservoir Storage Values')
plt.legend()
plt.show()

df1 = df[['PRCPUSC00045118', 'PRCPUSC00045933', 'PRCPUSC00046168',
       'PRCPUSC00049473', 'PRCPUSW00023233', 'PRCPUSW00093243',
       'TAVGUSC00045118', 'TAVGUSC00045933', 'TAVGUSC00046168',
       'TAVGUSC00049473', 'TAVGUSW00023233', 'TAVGUSW00093243',
       'TMAXUSC00045118', 'TMAXUSC00045933', 'TMAXUSC00046168',
       'TMAXUSC00049473', 'TMAXUSW00023233', 'TMAXUSW00093243',
       'TMINUSC00045118', 'TMINUSC00045933', 'TMINUSC00046168',
       'TMINUSC00049473', 'TMINUSW00023233', 'TMINUSW00093243', 'SUM_SWE',
       'storage']]

perm_importance = permutation_importance(rf, X_test, y_test)
sorted_idx = perm_importance.importances_mean.argsort()

feature_names = np.array(list(df1)[0:len(list(df1))-1])
plt.figure(figsize = (8,5))
plt.barh(feature_names[sorted_idx], perm_importance.importances_mean[sorted_idx])
plt.xlabel("Feature Importance")