"""
Structured error envelope (RFC-001, Convention 3).

Every API error responds with:
    { "error": { "code": "STABLE_CODE", "message": "human text", "details": null } }

`code` is what the frontend branches on. `message` can be reworded freely without
breaking any client logic — that's the whole point of separating the two.
"""

from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[dict[str, Any]] = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


# Common, reusable error constructors — keeps error codes consistent across endpoints.
def document_not_found(document_id: str) -> APIError:
    return APIError(404, "DOCUMENT_NOT_FOUND", f"No document found with id '{document_id}'.")


def unsupported_file_type(file_type: str) -> APIError:
    return APIError(
        400,
        "UNSUPPORTED_FILE_TYPE",
        f"File type '{file_type}' is not supported. Allowed: pdf, docx, txt, md.",
    )


def file_too_large(max_mb: int) -> APIError:
    return APIError(413, "FILE_TOO_LARGE", f"File exceeds the {max_mb}MB upload limit.")


def empty_query() -> APIError:
    return APIError(400, "EMPTY_QUERY", "Query cannot be empty.")


def llm_unavailable(detail: str = "") -> APIError:
    return APIError(502, "LLM_UNAVAILABLE", f"The language model is temporarily unavailable. {detail}".strip())
