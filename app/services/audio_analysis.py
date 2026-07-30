"""Shared decoding and duration helpers for audio analysis."""

from dataclasses import dataclass
from io import BytesIO

import librosa
import numpy as np
import soundfile as sf


class AudioAnalysisError(ValueError):
    """Raised when an audio analysis cannot be completed safely."""


class InvalidAudioError(AudioAnalysisError):
    """Raised when an uploaded file cannot be decoded as audio."""


@dataclass(frozen=True)
class DecodedAudio:
    """Audio samples in librosa's channel-first layout and their sample rate."""

    samples: np.ndarray
    sample_rate: int


def decode_audio(audio_bytes: bytes) -> DecodedAudio:
    """Decode uploaded audio bytes into a reusable analysis value object."""
    try:
        samples, sample_rate = sf.read(
            BytesIO(audio_bytes), dtype="float32", always_2d=False
        )
    except Exception as error:
        message = "The uploaded file is not a valid WAV audio file."
        raise InvalidAudioError(message) from error

    if samples.ndim == 2:
        samples = samples.T
    if samples.size == 0:
        raise InvalidAudioError("The uploaded WAV file contains no audio samples.")
    return DecodedAudio(samples=samples, sample_rate=sample_rate)


def decode_audio_samples(audio_bytes: bytes) -> tuple[np.ndarray, int]:
    """Decode audio bytes; retained as a convenient public compatibility helper."""
    audio = decode_audio(audio_bytes)
    return audio.samples, audio.sample_rate


def calculate_duration_seconds(audio_bytes: bytes) -> float:
    """Decode WAV audio and calculate its duration using librosa."""
    return calculate_duration_from_audio(decode_audio(audio_bytes))


def calculate_duration_from_audio(audio: DecodedAudio) -> float:
    """Calculate duration with librosa from already-decoded audio."""
    return float(librosa.get_duration(y=audio.samples, sr=audio.sample_rate))
