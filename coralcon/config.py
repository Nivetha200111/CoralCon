"""Runtime configuration helpers."""

import os


def is_sample_mode() -> bool:
    return os.getenv("CORAL_AVAILABLE", "false").lower() != "true"


def set_sample_mode(enabled: bool = True) -> None:
    os.environ["CORAL_AVAILABLE"] = "false" if enabled else "true"
