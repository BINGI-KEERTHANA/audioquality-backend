import logging
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import configure_logging, get_settings
from app.models import AnalyzeResponse, ErrorResponse, HealthResponse
from app.services.audio_analysis import (
    AudioAnalysisError,
    calculate_duration_from_audio,
    decode_audio,
)
from app.services.clipping_analysis import calculate_clipping_from_audio
from app.services.loudness_analysis import calculate_rms_loudness_from_audio
from app.services.noise_analysis import calculate_background_noise_from_audio
from app.services.scoring import calculate_overall_quality
from app.services.silence_analysis import calculate_silence_from_audio

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Quality Assessment API",
    version="1.0.0",
    description="Upload WAV audio for quality analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(status="ok")


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_413_CONTENT_TOO_LARGE: {"model": ErrorResponse},
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def analyze_audio(
    file: Annotated[UploadFile, File(description="WAV file to analyse")],
) -> AnalyzeResponse:
    """Analyse a WAV upload and return individual and combined quality metrics."""
    filename = file.filename or ""
    is_wav = filename.lower().endswith(".wav") or file.content_type in {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
    }
    if not is_wav:
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only WAV files are supported.",
        )

    try:
        audio_bytes = await file.read(settings.max_upload_bytes + 1)
        if len(audio_bytes) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"Upload exceeds the {settings.max_upload_bytes}-byte size limit."
                ),
            )

        audio = decode_audio(audio_bytes)
        duration_seconds = calculate_duration_from_audio(audio)
        loudness = calculate_rms_loudness_from_audio(audio)
        silence = calculate_silence_from_audio(audio)
        noise = calculate_background_noise_from_audio(audio)
        clipping = calculate_clipping_from_audio(audio)
        overall_quality = calculate_overall_quality(
            duration_seconds=duration_seconds,
            loudness_score=loudness.score,
            silence_score=silence.score,
            noise_score=noise.score,
            clipping_score=clipping.score,
        )
    except AudioAnalysisError as error:
        logger.info("audio_analysis_rejected filename=%s reason=%s", filename, error)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("audio_analysis_failed filename=%s", filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyse the uploaded audio.",
        ) from error
    finally:
        await file.close()

    return AnalyzeResponse(
        filename=filename,
        duration_seconds=duration_seconds,
        loudness_score=loudness.score,
        loudness_classification=loudness.classification,
        leading_silence_seconds=silence.leading_silence_seconds,
        trailing_silence_seconds=silence.trailing_silence_seconds,
        total_silence_seconds=silence.total_silence_seconds,
        silence_score=silence.score,
        silence_classification=silence.classification,
        noise_score=noise.score,
        noise_level_db=noise.level_db,
        noise_classification=noise.classification,
        clipping_percentage=clipping.percentage,
        clipping_score=clipping.score,
        clipping_classification=clipping.classification,
        overall_quality_score=overall_quality.score,
        recommendation=overall_quality.recommendation,
    )
