"""系统状态路由：健康检查、转写能力、频控、B 站登录态。"""

import os

from fastapi import APIRouter, Request

from app.config import (
    APP_VERSION,
    PARSE_RATE_LIMIT_PER_HOUR,
    QA_RATE_LIMIT_PER_HOUR,
    SUMMARY_RATE_LIMIT_PER_HOUR,
    TRANSCRIBE_RATE_LIMIT_PER_HOUR,
)
from app.http_utils import get_client_key, get_rate_limit_config
from app.schemas import (
    AsrStatusResponse,
    BilibiliAuthStatusResponse,
    HealthResponse,
    RateLimitStatusResponse,
)
from app.services.asr_service import DEFAULT_ASR_MODEL
from app.services.bilibili_service import get_bilibili_auth_status
from app.services.rate_limit_service import get_rate_limit_items
from app.services.sensevoice_service import (
    DEFAULT_SENSEVOICE_MODEL,
    get_sensevoice_status,
)
from app.services.transcript_correction_service import (
    get_transcript_correction_status,
)

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """
    返回本地服务状态。
    """
    return HealthResponse(status="ok", mode="local", version=APP_VERSION)


@router.get("/asr/status", response_model=AsrStatusResponse)
def get_asr_status() -> AsrStatusResponse:
    """返回本地转写能力状态。"""
    sensevoice_available, sensevoice_message = get_sensevoice_status()
    correction_available, correction_message = get_transcript_correction_status()
    return AsrStatusResponse(
        recommended_engine=(
            "sensevoice_small" if sensevoice_available else "local_whisper"
        ),
        whisper_model=(
            os.getenv("ASR_WHISPER_MODEL", "").strip() or DEFAULT_ASR_MODEL
        ),
        sensevoice_available=sensevoice_available,
        sensevoice_model=(
            os.getenv("SENSEVOICE_MODEL", "").strip()
            or DEFAULT_SENSEVOICE_MODEL
        ),
        sensevoice_message=sensevoice_message,
        correction_available=correction_available,
        correction_message=correction_message,
    )


@router.get("/rate-limit/status", response_model=RateLimitStatusResponse)
def get_rate_limit_status(request: Request) -> RateLimitStatusResponse:
    """
    返回当前客户端的本地频控状态。
    """
    return RateLimitStatusResponse(
        items=get_rate_limit_items(
            client_key=get_client_key(request),
            action_limits=get_rate_limit_config(
                PARSE_RATE_LIMIT_PER_HOUR,
                SUMMARY_RATE_LIMIT_PER_HOUR,
                QA_RATE_LIMIT_PER_HOUR,
                TRANSCRIBE_RATE_LIMIT_PER_HOUR,
            ),
        )
    )


@router.get("/bilibili/auth/status", response_model=BilibiliAuthStatusResponse)
def get_bilibili_local_auth_status() -> BilibiliAuthStatusResponse:
    """
    返回本地显式 B 站 Cookie 配置是否可被 nav 接口识别。
    """
    return get_bilibili_auth_status()
