"""녹취 파일 받아쓰기 (02-specs 3 · 4절)."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app import gemini
from app.config import ALLOWED_AUDIO_TYPES, MAX_UPLOAD_BYTES
from app.schemas import UploadOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", response_model=UploadOut)
def upload_audio(file: UploadFile) -> UploadOut:
    suffix = Path(file.filename or "").suffix.lower()
    mime_type = ALLOWED_AUDIO_TYPES.get(suffix)
    if mime_type is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="mp3, wav 파일만 받습니다")

    # 한도보다 1바이트 더 읽어 25MB 초과를 가린다
    audio = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(audio) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="25MB 이하 파일만 받습니다")

    try:
        text = gemini.transcribe(audio, mime_type)
    except gemini.GeminiError as exc:
        logger.exception("받아쓰기 실패")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="받아쓰기 서비스 호출에 실패했습니다") from exc
    return UploadOut(body=text)
