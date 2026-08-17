"""媒体资源路由：封面图代理。"""

import logging

from fastapi import APIRouter, HTTPException, Query, Response

from app.config import (
    IMAGE_PROXY_ACCEPT_HEADER,
    IMAGE_PROXY_MAX_BYTES,
    IMAGE_PROXY_TIMEOUT_SECONDS,
)
from app.services import http_fetch_service

router = APIRouter(prefix="/api", tags=["media"])

logger = logging.getLogger(__name__)


@router.get("/image-proxy")
def proxy_public_image(
    url: str = Query(min_length=8, max_length=2048),
) -> Response:
    """
    代理公开封面图，避免浏览器直连远端 CDN 时被防盗链或本机 TLS 链路拦截。
    """
    try:
        image_body, content_type = http_fetch_service.fetch_public_bytes(
            url,
            accept_header=IMAGE_PROXY_ACCEPT_HEADER,
            timeout_seconds=IMAGE_PROXY_TIMEOUT_SECONDS,
            max_bytes=IMAGE_PROXY_MAX_BYTES,
        )
    except OSError as error:
        logger.warning("image proxy fetch failed: %s", error.__class__.__name__)
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "IMAGE_PROXY_FAILED",
                "message": "封面图片读取失败，请稍后重试。",
            },
        ) from error

    media_type = content_type.split(";", 1)[0].strip().lower()
    if not media_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "IMAGE_PROXY_INVALID_TYPE",
                "message": "该链接返回的不是图片内容。",
            },
        )

    return Response(
        content=image_body,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
