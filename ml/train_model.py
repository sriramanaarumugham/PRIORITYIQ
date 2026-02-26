import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import pickle
import os

data = {
    'urgency': [5,4,3,2,1,5,4,3,2,1],
    'complexity': [3,4,5,2,1,3,4,5,2,1],
    'est_hours': [2,5,8,3,1,2,6,9,3,2],
    'deadline_days': [1,2,5,7,10,1,3,6,8,12],
    'priority_label': [2,2,1,0,0,2,1,1,0,0]
}

df = pd.DataFrame(data)

X = df[['urgency','complexity','est_hours','deadline_days']]
y = df['priority_label']

model = DecisionTreeClassifier(random_state=42)
model.fit(X, y)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")

