# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 13:26:55 2026

@author: ROHIT
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import numpy as np

# 1. Load and Prepare
df = pd.read_csv('data.csv')
# Convert words to numbers so AI can read them
df_encoded = pd.get_dummies(df, columns=['city', 'furnishing'], drop_first=True)

# 2. Define Features (X) and Target (y)
X = df_encoded.drop(['rent', 'house_type', 'locality'], axis=1)
y = df_encoded['rent']

# 3. Train the Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. GET THE "WHY": Feature Importance
importances = model.feature_importances_
feature_names = X.columns
indices = np.argsort(importances)

plt.figure(figsize=(10,6))
plt.title('Why do prices vary? (Key Drivers of Rent)')
plt.barh(range(len(indices)), importances[indices], align='center')
plt.yticks(range(len(indices)), [feature_names[i] for i in indices])
plt.xlabel('Importance Score')
plt.show()

print("Observation: Check the plot! Usually, 'Area' or 'City_Mumbai' will be the highest.")