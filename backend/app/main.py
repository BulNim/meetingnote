"""MeetingNote 백엔드 진입점. 실행: backend/ 에서 uvicorn app.main:app --port 8000"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.database import Base, engine
from app.routers import notes, todos, upload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MeetingNote")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """검증 실패는 400. 스펙 외 필드(extra_forbidden)만 422 로 남긴다 (02-specs 4.1)."""
    errors = exc.errors()
    has_extra_field = any(error.get("type") == "extra_forbidden" for error in errors)
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT if has_extra_field else status.HTTP_400_BAD_REQUEST
    detail = [{"loc": error.get("loc"), "msg": error.get("msg"), "type": error.get("type")} for error in errors]
    return JSONResponse(status_code=status_code, content={"detail": detail})


app.include_router(notes.router)
app.include_router(todos.router)
app.include_router(upload.router)

# 프론트는 같은 오리진에서 제공한다. API 라우터 뒤에 붙여야 /api/ 를 가리지 않는다
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True, check_dir=False), name="frontend")
