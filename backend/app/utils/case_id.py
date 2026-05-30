"""
SmartRescue AI — Case ID Generator
Generates unique emergency case IDs in format: SR-YYYYMMDD-XXXXX
"""

import random
import string
from datetime import datetime, timezone


def generate_case_id() -> str:
    """
    Generate a unique case ID in format: SR-YYYYMMDD-XXXXX
    
    Example: SR-20260522-A7K3M
    """
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=5)
    )
    return f"SR-{date_part}-{random_part}"


def generate_notification_id() -> str:
    """Generate a unique notification ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"NTF-{timestamp}-{random_part}"


def generate_accident_id() -> str:
    """Generate a unique accident record ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ACC-{timestamp}-{random_part}"
