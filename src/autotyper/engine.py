"""Platform independent, interruptible typing control."""
from dataclasses import dataclass
import math
import threading
from typing import Callable


@dataclass(frozen=True)
class Settings:
    speed: float = 20
    delay: float = 5

    def __post_init__(self):
        if not math.isfinite(self.speed) or not 1 <= self.speed <= 200:
            raise ValueError("Speed must be between 1 and 200 characters per second.")
        if not math.isfinite(self.delay) or not 1 <= self.delay <= 60:
            raise ValueError("Start delay must be between 1 and 60 seconds.")


def type_text(text: str, settings: Settings, stop: threading.Event,
              send: Callable[[str], None], report: Callable[[str], None]) -> bool:
    """Return True on completion, False on cancellation. Propagate backend errors."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text:
        raise ValueError("Enter some text first.")
    remaining = settings.delay
    while remaining > 0:
        report(f"Starting in {math.ceil(remaining)} seconds — select the target window. F8 stops.")
        step = min(1, remaining)
        if stop.wait(step):
            report("Stopped.")
            return False
        remaining -= step
    for index, char in enumerate(text):
        if stop.is_set():
            report("Stopped.")
            return False
        send(char)
        report(f"Typing {index + 1}/{len(text)} — F8 stops.")
        if index + 1 < len(text) and stop.wait(1 / settings.speed):
            report("Stopped.")
            return False
    report(f"Completed: {len(text)} characters.")
    return True
