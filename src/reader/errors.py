from __future__ import annotations

from typing import Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from reader.models.schemas import ProblemDetail


class APIError(Exception):
    def __init__(
        self,
        status: int,
        detail: str,
        title: Optional[str] = None,
        type_uri: str = "about:blank",
        **extras,
    ):
        self.status = status
        self.detail = detail
        self.title = title
        self.type_uri = type_uri
        self.extras = extras


def not_found(detail: str = "Resource not found") -> APIError:
    return APIError(404, detail, title="Not Found")


def conflict(detail: str = "Resource already exists", **extras) -> APIError:
    return APIError(409, detail, title="Conflict", **extras)


def forbidden(detail: str = "Forbidden") -> APIError:
    return APIError(403, detail, title="Forbidden")


def unprocessable(detail: str) -> APIError:
    return APIError(422, detail, title="Unprocessable Entity")


def bad_gateway(detail: str) -> APIError:
    return APIError(502, detail, title="Bad Gateway")


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    body = ProblemDetail(
        type=exc.type_uri,
        title=exc.title,
        status=exc.status,
        detail=exc.detail,
        **exc.extras,
    )
    return JSONResponse(
        status_code=exc.status,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    body = ProblemDetail(
        status=422,
        title="Validation Error",
        detail=str(exc.errors()),
    )
    return JSONResponse(
        status_code=422,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
