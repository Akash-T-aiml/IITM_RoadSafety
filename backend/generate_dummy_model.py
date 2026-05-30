"""
SmartRescue AI — Mock RandomForest Model Generator
Generates a trained RandomForestClassifier pickle file containing the exact columns
and feature names required by the SmartRescue AI backend.
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

# Define the exact features expected
FEATURE_COLUMNS = [
    "accelerometer_x", "accelerometer_y", "accelerometer_z",
    "gyroscope_x", "gyroscope_y", "gyroscope_z",
    "speed",
    "heart_rate",
    "orientation_x", "orientation_y", "orientation_z"
]


def generate_dummy_model():
    print("Generating mock accident classification dataset...")
    
    # Create random training data
    # 0 = No Accident, 1 = Minor Accident, 2 = Severe Accident
    np.random.seed(42)
    n_samples = 1000
    
    X = np.random.randn(n_samples, len(FEATURE_COLUMNS))
    y = np.zeros(n_samples, dtype=int)
    
    # Speed is feature index 6
    # Accel_x, Accel_y, Accel_z are index 0, 1, 2
    # Gyro_x, Gyro_y, Gyro_z are index 3, 4, 5
    
    # Map features to generate mock labels:
    for i in range(n_samples):
        if i < 400:
            # Class 0: No Accident
            X[i, 0] = np.random.uniform(-2.0, 2.0)   # acc x
            X[i, 1] = np.random.uniform(-9.8, -9.0)  # acc y (gravity)
            X[i, 2] = np.random.uniform(-2.0, 2.0)   # acc z
            X[i, 3] = np.random.uniform(-0.1, 0.1)   # gyro x
            X[i, 4] = np.random.uniform(-0.1, 0.1)   # gyro y
            X[i, 5] = np.random.uniform(-0.1, 0.1)   # gyro z
            X[i, 6] = np.random.uniform(0.0, 50.0)   # speed
            X[i, 7] = np.random.uniform(60.0, 90.0)  # HR
            X[i, 8] = np.random.uniform(-0.2, 0.2)   # pitch
            X[i, 9] = np.random.uniform(-0.2, 0.2)   # roll
            X[i, 10] = np.random.uniform(-3.14, 3.14)# yaw
            y[i] = 0
        elif i < 750:
            # Class 1: Minor Accident
            X[i, 0] = np.random.uniform(-10.0, 10.0)
            X[i, 1] = np.random.uniform(-15.0, 15.0)
            X[i, 2] = np.random.uniform(-10.0, 10.0)
            X[i, 3] = np.random.uniform(-1.5, 1.5)
            X[i, 4] = np.random.uniform(-1.5, 1.5)
            X[i, 5] = np.random.uniform(-1.5, 1.5)
            X[i, 6] = np.random.uniform(30.0, 80.0)
            X[i, 7] = np.random.uniform(85.0, 110.0)
            X[i, 8] = np.random.uniform(-1.0, 1.0)
            X[i, 9] = np.random.uniform(-1.0, 1.0)
            X[i, 10] = np.random.uniform(-3.14, 3.14)
            y[i] = 1
        else:
            # Class 2: Severe Accident
            X[i, 0] = np.random.uniform(-35.0, 35.0)
            X[i, 1] = np.random.uniform(-40.0, 40.0)
            X[i, 2] = np.random.uniform(-35.0, 35.0)
            X[i, 3] = np.random.uniform(-4.0, 4.0)
            X[i, 4] = np.random.uniform(-4.0, 4.0)
            X[i, 5] = np.random.uniform(-4.0, 4.0)
            X[i, 6] = np.random.uniform(60.0, 130.0)
            X[i, 7] = np.random.uniform(110.0, 160.0)
            X[i, 8] = np.random.uniform(-2.5, 2.5)
            X[i, 9] = np.random.uniform(-2.5, 2.5)
            X[i, 10] = np.random.uniform(-3.14, 3.14)
            y[i] = 2

    print(f"Dataset generated. Class distribution: No Accident={sum(y==0)}, Minor={sum(y==1)}, Severe={sum(y==2)}")
    
    # Train RandomForest model
    print("Training RandomForest model classifier...")
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)
    
    # Attach feature names attribute explicitly
    clf.feature_names_in_ = np.array(FEATURE_COLUMNS)
    
    # Ensure folder exists
    os.makedirs("./ml_models", exist_ok=True)
    
    # Save model
    model_path = "./ml_models/smartrescue_final_model.pkl"
    joblib.dump(clf, model_path)
    print(f"Model successfully saved to: {os.path.abspath(model_path)}")
    
    # Test reloading
    loaded = joblib.load(model_path)
    print(f"Model verification successful. Features expected: {list(loaded.feature_names_in_)}")


if __name__ == "__main__":
    generate_dummy_model()
