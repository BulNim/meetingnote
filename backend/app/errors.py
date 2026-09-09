from fastapi import HTTPException


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "회의록을 찾을 수 없습니다.") -> None:
        super().__init__(status_code=404, detail=detail)


class GeminiError(HTTPException):
    def __init__(self, detail: str = "받아쓰기 또는 분석에 실패했습니다.") -> None:
        super().__init__(status_code=502, detail=detail)
