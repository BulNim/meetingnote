from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES
from ..dependencies import get_gemini_service
from ..schemas import UploadResponse
from ..services.gemini_service import GeminiService, GeminiServiceError

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
def upload_audio(
    file: UploadFile = File(...),
    gemini: GeminiService = Depends(get_gemini_service),
) -> UploadResponse:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="mp3 또는 wav 파일만 업로드할 수 있습니다.")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="파일 크기는 25MB 이하여야 합니다.")
    try:
        text = gemini.transcribe(data, file.filename or "audio" )
    except GeminiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return UploadResponse(text=text)
