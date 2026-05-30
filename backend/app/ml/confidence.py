"""
SmartRescue AI — Confidence Scoring & Escalation Logic
Evaluates prediction confidence and manages false alarm filtering.
"""

from typing import Dict, Any, Optional, List
from collections import defaultdict

import numpy as np

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConfidenceEvaluator:
    """
    Evaluates ML prediction confidence and determines emergency escalation level.
    
    Confidence Thresholds:
        > 0.85 (AUTO_TRIGGER)  → Auto-trigger emergency workflow
        0.50 - 0.85 (ASK)     → Ask user for confirmation  
        < 0.50 (NO_ACTION)    → No action, likely false alarm
    
    False Alarm Filtering:
        Requires N consecutive severe predictions before triggering.
    """

    ESCALATION_AUTO = "auto_triggered"
    ESCALATION_CONFIRM = "confirmation_needed"
    ESCALATION_NONE = "no_emergency"

    def __init__(self):
        # Per-user buffer of consecutive severe predictions
        self._prediction_buffers: Dict[str, List[int]] = defaultdict(list)
        settings = get_settings()
        self.auto_threshold = settings.CONFIDENCE_AUTO_TRIGGER
        self.ask_threshold = settings.CONFIDENCE_ASK_THRESHOLD
        self.buffer_size = settings.FALSE_ALARM_BUFFER_SIZE

    def evaluate_confidence(
        self, probabilities: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate prediction confidence from probability array.
        
        Args:
            probabilities: Array of [p_no_accident, p_minor, p_severe]
        
        Returns:
            Dict with confidence_score, emergency_status, and class probabilities.
        """
        if len(probabilities) < 3:
            return {
                "confidence_score": 0.0,
                "emergency_status": self.ESCALATION_NONE,
                "probabilities": {},
            }

        predicted_class = int(np.argmax(probabilities))
        confidence_score = float(np.max(probabilities))

        class_probs = {
            "no_accident": round(float(probabilities[0]), 4),
            "minor_accident": round(float(probabilities[1]), 4),
            "severe_accident": round(float(probabilities[2]), 4),
        }

        # Determine escalation level
        if predicted_class == 2 and confidence_score >= self.auto_threshold:
            emergency_status = self.ESCALATION_AUTO
        elif predicted_class >= 1 and confidence_score >= self.ask_threshold:
            emergency_status = self.ESCALATION_CONFIRM
        else:
            emergency_status = self.ESCALATION_NONE

        return {
            "confidence_score": round(confidence_score, 4),
            "emergency_status": emergency_status,
            "probabilities": class_probs,
            "predicted_class": predicted_class,
        }

    def update_buffer(self, user_id: str, prediction: int) -> Dict[str, Any]:
        """
        Update the per-user prediction buffer for false alarm filtering.
        
        Returns buffer status info including whether emergency should be triggered.
        """
        buffer = self._prediction_buffers[user_id]
        buffer.append(prediction)

        # Keep only the last N predictions
        if len(buffer) > self.buffer_size * 2:
            self._prediction_buffers[user_id] = buffer[-self.buffer_size:]
            buffer = self._prediction_buffers[user_id]

        # Count consecutive severe predictions (from the end)
        consecutive_severe = 0
        for p in reversed(buffer):
            if p == 2:
                consecutive_severe += 1
            else:
                break

        # Count consecutive non-normal (severe or minor)
        consecutive_abnormal = 0
        for p in reversed(buffer):
            if p >= 1:
                consecutive_abnormal += 1
            else:
                break

        should_trigger = consecutive_severe >= self.buffer_size
        should_ask = (
            not should_trigger
            and consecutive_abnormal >= self.buffer_size
        )

        if should_trigger:
            buffer_status = "emergency_triggered"
        elif should_ask:
            buffer_status = "alert_pending"
        elif consecutive_severe > 0 or consecutive_abnormal > 0:
            buffer_status = "monitoring"
        else:
            buffer_status = "buffering"

        return {
            "consecutive_severe_count": consecutive_severe,
            "consecutive_abnormal_count": consecutive_abnormal,
            "buffer_size": len(buffer),
            "should_trigger": should_trigger,
            "should_ask_confirmation": should_ask,
            "buffer_status": buffer_status,
        }

    def clear_buffer(self, user_id: str):
        """Clear prediction buffer for a user (after emergency resolved or false alarm)."""
        if user_id in self._prediction_buffers:
            del self._prediction_buffers[user_id]
            logger.info(f"Cleared prediction buffer for user {user_id}")

    def get_buffer_status(self, user_id: str) -> Dict[str, Any]:
        """Get current buffer status for a user."""
        buffer = self._prediction_buffers.get(user_id, [])
        return {
            "user_id": user_id,
            "buffer_length": len(buffer),
            "recent_predictions": buffer[-5:] if buffer else [],
        }


# Global singleton instance
confidence_evaluator = ConfidenceEvaluator()
