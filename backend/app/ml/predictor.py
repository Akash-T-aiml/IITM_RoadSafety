"""
SmartRescue AI — ML Prediction Service
Loads trained RandomForest model and provides accident prediction.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import joblib

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AccidentPredictor:
    """
    Accident severity predictor using a trained RandomForest model.
    Loaded once at startup and reused for all predictions.
    """

    # Default feature order for the model
    FEATURE_COLUMNS = [
        "accelerometer_x", "accelerometer_y", "accelerometer_z",
        "gyroscope_x", "gyroscope_y", "gyroscope_z",
        "speed",
        "heart_rate",
        "orientation_x", "orientation_y", "orientation_z",
    ]

    PREDICTION_LABELS = {
        0: "No Accident",
        1: "Minor Accident",
        2: "Severe Accident",
    }

    def __init__(self):
        self.model = None
        self.model_loaded = False
        self._feature_columns = self.FEATURE_COLUMNS.copy()

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Load the trained model from disk.
        Falls back to a mock predictor if the model file is not found.
        """
        settings = get_settings()
        path = model_path or settings.ML_MODEL_PATH

        try:
            if os.path.exists(path):
                self.model = joblib.load(path)
                self.model_loaded = True
                logger.info(f"ML model loaded from {path}")

                # Try to detect feature names from model
                if hasattr(self.model, "feature_names_in_"):
                    self._feature_columns = list(self.model.feature_names_in_)
                    logger.info(f"Model expects features: {self._feature_columns}")

                return True
            else:
                logger.warning(
                    f"Model file not found at {path}. Using mock predictor."
                )
                self.model_loaded = False
                return False
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.model_loaded = False
            return False

    def extract_features(self, sensor_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract and order features from sensor data dictionary.
        Missing features are filled with 0.0.
        """
        features = []
        for col in self._feature_columns:
            value = sensor_data.get(col, 0.0)
            if value is None:
                value = 0.0
            features.append(float(value))

        return np.array([features])

    def predict(self, sensor_data: Dict[str, Any]) -> Tuple[int, np.ndarray]:
        """
        Run prediction on sensor data.
        
        Args:
            sensor_data: Dictionary of sensor values
            
        Returns:
            Tuple of (prediction_label: int, probabilities: ndarray)
            prediction_label: 0=No Accident, 1=Minor, 2=Severe
        """
        features = self.extract_features(sensor_data)

        if self.model_loaded and self.model is not None:
            prediction = int(self.model.predict(features)[0])
            probabilities = self.model.predict_proba(features)[0]
        else:
            # Mock prediction based on sensor value heuristics
            prediction, probabilities = self._mock_predict(sensor_data)

        logger.info(
            f"Prediction: {prediction} ({self.PREDICTION_LABELS.get(prediction)}), "
            f"Probabilities: {probabilities.tolist()}"
        )

        return prediction, probabilities

    def _mock_predict(self, sensor_data: Dict[str, Any]) -> Tuple[int, np.ndarray]:
        """
        Mock prediction when no model is loaded.
        Uses simple heuristics based on accelerometer magnitude and speed.
        """
        acc_x = abs(sensor_data.get("accelerometer_x", 0))
        acc_y = abs(sensor_data.get("accelerometer_y", 0))
        acc_z = abs(sensor_data.get("accelerometer_z", 0))
        speed = sensor_data.get("speed", 0)

        # Calculate accelerometer magnitude
        acc_magnitude = (acc_x**2 + acc_y**2 + acc_z**2) ** 0.5

        # Simple threshold-based classification
        if acc_magnitude > 30 and speed > 50:
            return 2, np.array([0.05, 0.10, 0.85])
        elif acc_magnitude > 20 or (acc_magnitude > 15 and speed > 40):
            return 1, np.array([0.15, 0.70, 0.15])
        else:
            return 0, np.array([0.90, 0.07, 0.03])

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        info = {
            "model_loaded": self.model_loaded,
            "feature_columns": self._feature_columns,
            "prediction_labels": self.PREDICTION_LABELS,
        }

        if self.model_loaded and self.model is not None:
            info["model_type"] = type(self.model).__name__
            if hasattr(self.model, "n_estimators"):
                info["n_estimators"] = self.model.n_estimators
            if hasattr(self.model, "n_features_in_"):
                info["n_features"] = self.model.n_features_in_

        return info


# Global singleton instance
predictor = AccidentPredictor()
