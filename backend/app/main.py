from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


from .database import Base, engine
from .routers import notes, todos, upload


app = FastAPI(title="MeetingNote API")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    status_code = 422 if any(
        error.get("type") == "extra_forbidden" for error in exc.errors()
    ) else 400
    return JSONResponse(status_code=status_code, content={"detail": exc.errors()})


app.include_router(notes.router)
app.include_router(todos.router)
app.include_router(upload.router)

if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
