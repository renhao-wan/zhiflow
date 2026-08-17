import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import APP_VERSION, FRONTEND_ORIGINS
from app.http_utils import build_api_error_response
from app.routers import (
    correction_terms,
    demo,
    download,
    generate,
    library,
    media,
    parse,
    system,
    transcribe,
)
from app.schemas import ApiError

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZhiFlow Media Assistant API",
    version=APP_VERSION,
    description="本地优先的 AI 媒体内容解析总结工作台后端服务。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(FRONTEND_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

for module in (
    system,
    correction_terms,
    media,
    demo,
    library,
    parse,
    generate,
    transcribe,
    download,
):
    app.include_router(module.router)


@app.exception_handler(HTTPException)
def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    """
    将业务异常统一转换为前端可直接读取的错误结构。
    """
    detail = exc.detail
    if isinstance(detail, dict):
        return build_api_error_response(
            status_code=exc.status_code,
            error_code=str(detail.get("error_code", "HTTP_ERROR")),
            message=str(detail.get("message", "请求失败，请稍后重试。")),
        )

    return build_api_error_response(
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        message="请求失败，请稍后重试。",
    )


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    隐藏 Pydantic 内部校验细节，只给前端稳定错误结构。
    """
    return build_api_error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="请求参数不完整或格式不正确。",
    )
