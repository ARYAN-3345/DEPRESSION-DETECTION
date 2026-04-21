import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# -------------------------------
# LOAD DATASET
# -------------------------------

df = pd.read_csv("C:\\Users\\shrey\\OneDrive\\Desktop\\MiniProject\\DEPRESSION-DETECTION\\BACKEND\\Data\\quiz_dataset.csv.csv")  # CHANGE NAME

# -------------------------------
# SELECT ONLY PHQ COLUMNS
# -------------------------------

phq_cols = ['phq1','phq2','phq3','phq4','phq5','phq6','phq7','phq8','phq9']
df = df[phq_cols]

# -------------------------------
# HANDLE MISSING VALUES
# -------------------------------

df = df.fillna(0)

# -------------------------------
# CREATE LABEL (IMPORTANT)
# -------------------------------

df['total_score'] = df.sum(axis=1)

def get_label(score):
    if score <= 7:
        return 0   # Low
    elif score <= 14:
        return 1   # Medium
    else:
        return 2   # High

df['label'] = df['total_score'].apply(get_label)

# -------------------------------
# FEATURES & TARGET
# -------------------------------

X = df[phq_cols]
y = df['label']

# -------------------------------
# TRAIN TEST SPLIT
# -------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------------
# TRAIN MODEL
# -------------------------------

model = GaussianNB()
model.fit(X_train, y_train)

print("Model trained successfully!")

# -------------------------------
# EVALUATION
# -------------------------------

y_pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# -------------------------------
# SAVE MODEL
# -------------------------------

os.makedirs("backend/models", exist_ok=True)
joblib.dump(model, "backend/models/quiz_model.pkl")

print("\nModel saved at backend/models/quiz_model.pkl")