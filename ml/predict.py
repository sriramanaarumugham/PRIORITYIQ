import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    features = [[4,3,5,3]]
    label = model.predict(features)[0]
    label_map = {2:"High", 1:"Medium", 0:"Low"}
    print("Predicted:", label_map[int(label)])
except FileNotFoundError:
    print("Model file not found. Run train_model.py first.")
except Exception as e:
    print(f"Error loading model: {e}")
