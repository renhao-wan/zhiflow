"""跨路由复用的 HTTP 层工具函数。"""

import os
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas import ApiError

PUBLIC_URL_PATTERN = re.compile(r"https?://[^\s，。；;、]+")
BILIBILI_VIDEO_PATH_PATTERN = re.compile(r"^/video/(BV[a-zA-Z0-9]+)")
BILIBILI_ALLOWED_QUERY_KEYS = {"p", "t"}


def extract_public_url(raw_text: str) -> str:
    """
    支持抖音分享口令这类整段文案输入，优先提取其中第一个公开链接。
    """
    stripped_text = raw_text.strip()
    match = PUBLIC_URL_PATTERN.search(stripped_text)
    if not match:
        return stripped_text

    return match.group(0).rstrip(").,，。；;、")


def normalize_bilibili_video_url(video_url: str) -> str:
    """
    清理 B 站分享链接里的跟踪参数，降低公开解析被平台快速拒绝的概率。
    """
    parsed_url = urlparse(video_url)
    hostname = parsed_url.hostname or ""
    if not (
        hostname.endswith("bilibili.com") or hostname.endswith("b23.tv")
    ):
        return video_url

    match = BILIBILI_VIDEO_PATH_PATTERN.search(parsed_url.path)
    if not match:
        return video_url

    safe_query = [
        (key, value)
        for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)
        if key in BILIBILI_ALLOWED_QUERY_KEYS and value
    ]
    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            f"/video/{match.group(1)}",
            "",
            urlencode(safe_query),
            "",
        )
    )


def normalize_public_video_url(raw_url: str) -> str:
    """
    从用户输入中提取并规范化媒体 URL。
    """
    video_url = extract_public_url(raw_url)
    parsed_url = urlparse(video_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "INVALID_URL",
                "message": "请输入以 http:// 或 https:// 开头的公开媒体链接。",
            },
        )

    return normalize_bilibili_video_url(video_url)


def get_client_key(request: Request) -> str:
    """
    获取本地频控使用的客户端标识。
    """
    return request.client.host if request.client else "local"


def get_rate_limit_config(
    parse_per_hour: int,
    summarize_per_hour: int,
    qa_per_hour: int,
    transcribe_per_hour: int,
) -> dict[str, int]:
    """
    返回当前本地频控配置。
    """
    return {
        "parse": parse_per_hour,
        "summarize": summarize_per_hour,
        "qa": qa_per_hour,
        "transcribe": transcribe_per_hour,
    }


def enforce_rate_limit(request: Request, action: str, limit: int) -> None:
    """
    个人本地使用阶段不限制高成本动作。
    """
    _ = (request, action, limit)
    return


def build_api_error_response(
    status_code: int, error_code: str, message: str
) -> JSONResponse:
    """
    构造统一错误响应。
    """
    return JSONResponse(
        status_code=status_code,
        content=ApiError(error_code=error_code, message=message).model_dump(),
    )


def read_int_env(name: str, default_value: int) -> int:
    """
    读取整数环境变量，格式错误时使用默认值。
    """
    try:
        return int(os.getenv(name, str(default_value)))
    except ValueError:
        return default_value
