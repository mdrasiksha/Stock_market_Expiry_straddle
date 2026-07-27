"""Runtime generation for alert sounds without storing binary files in git."""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 8_000
DURATION_SECONDS = 0.35
AMPLITUDE = 12_000


def ensure_default_sound(path: Path, frequency: int) -> Path:
    """Create a small WAV alert file when it is missing and return its path."""
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(SAMPLE_RATE * DURATION_SECONDS)
    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        frames = []
        for index in range(frame_count):
            value = int(AMPLITUDE * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
            frames.append(struct.pack("<h", value))
        wav_file.writeframes(b"".join(frames))
    return path


def ensure_alert_sounds(success_path: Path, alarm_path: Path) -> None:
    """Ensure success and alarm WAV files are available for Streamlit playback."""
    ensure_default_sound(success_path, frequency=880)
    ensure_default_sound(alarm_path, frequency=440)
