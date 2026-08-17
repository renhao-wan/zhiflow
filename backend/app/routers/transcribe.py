"""本地转写路由。"""

import logging
import sqlite3
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request

from app.config import TRANSCRIBE_RATE_LIMIT_PER_HOUR
from app.http_utils import enforce_rate_limit, normalize_public_video_url
from app.schemas import TranscribeRequest, TranscribeResponse
from app.services.asr_service import transcribe_media_audio
from app.services.bilibili_service import (
    is_bilibili_url,
    resolve_bilibili_transcription_source,
)
from app.services.correction_term_service import (
    CorrectionTermError,
    record_term_usage,
)
from app.services.douyin_service import (
    create_douyin_transcription_downloader,
    is_douyin_url,
)
from app.services.library_service import (
    get_library_detail_by_source_url,
    update_transcript_for_source_url,
)
from app.services.media_source_service import parse_media_source
from app.services.xiaohongshu_service import is_xiaohongshu_url

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])

logger = logging.getLogger(__name__)


@router.post("", response_model=TranscribeResponse)
def transcribe_video(
    request: Request,
    transcribe_request: TranscribeRequest,
) -> TranscribeResponse:
    """
    当平台没有现成文字时，按用户选择使用本地 ASR 生成转写稿。
    """
    video_url = normalize_public_video_url(transcribe_request.url)
    transcribe_context = _get_transcribe_prompt_context(video_url)
    is_douyin_source = is_douyin_url(video_url)
    transcribe_source_url, transcribe_http_headers = _resolve_transcription_source(
        video_url
    )
    enforce_rate_limit(request, "transcribe", TRANSCRIBE_RATE_LIMIT_PER_HOUR)
    transcribe_response = transcribe_media_audio(
        video_url=transcribe_source_url,
        video_id=transcribe_request.video_id,
        http_headers=transcribe_http_headers,
        audio_downloader_factory=(
            create_douyin_transcription_downloader if is_douyin_source else None
        ),
        response_source_url=video_url,
        media_title=transcribe_context.get("title"),
        media_author=transcribe_context.get("author"),
        media_platform=transcribe_context.get("platform"),
        media_type=transcribe_context.get("media_type"),
        context_settings=transcribe_request.context_settings,
        shownotes_plain_text=transcribe_context.get("shownotes_plain_text"),
        asr_engine=transcribe_request.asr_engine,
    )
    try:
        update_transcript_for_source_url(
            video_url,
            transcribe_response.transcript,
            transcribe_response.transcript_variant_key,
            transcribe_response.shownotes_context,
        )
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning(
            "library transcript update failed: %s",
            error.__class__.__name__,
        )

    correction_terms = (
        transcribe_request.context_settings.correction_terms
        if transcribe_request.context_settings
        else []
    )
    try:
        record_term_usage(correction_terms)
    except (CorrectionTermError, sqlite3.Error, OSError) as error:
        # 术语统计属于辅助记录，不能覆盖已经成功生成的转写稿。
        logger.warning(
            "correction term usage update failed: %s",
            error.__class__.__name__,
        )

    return transcribe_response


def _get_transcribe_prompt_context(source_url: str) -> dict[str, object]:
    """
    从本地历史读取媒体上下文，用于 ASR hotwords / prompt；读取失败不阻断转写。
    """
    try:
        detail = get_library_detail_by_source_url(source_url)
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning(
            "library context lookup failed for transcription: %s",
            error.__class__.__name__,
        )
        return {}

    if detail is None:
        return {}

    shownotes_plain_text = detail.shownotes_plain_text
    if (
        not shownotes_plain_text
        and detail.video.text_source_type == "shownotes"
    ):
        # 兼容功能上线前的旧历史：当时 shownotes 只存在 transcript.plain_text。
        shownotes_plain_text = detail.transcript.plain_text

    return {
        "title": detail.video.title,
        "author": detail.video.author,
        "platform": detail.video.platform,
        "media_type": detail.video.media_type,
        "shownotes_plain_text": shownotes_plain_text,
    }


def _resolve_transcription_source(
    source_url: str,
) -> tuple[str, dict[str, str] | None]:
    """
    页面 URL 通常不是可直接转写的媒体文件，先通过专用适配器取公开媒体直链。
    """
    if is_bilibili_url(source_url):
        bilibili_source = resolve_bilibili_transcription_source(source_url)
        return bilibili_source.audio_url, bilibili_source.http_headers

    if is_douyin_url(source_url):
        # 抖音媒体流必须在解析详情的匿名 Edge 上下文中获取，不能把短时直链交给 yt-dlp。
        return source_url, None

    hostname = urlparse(source_url).hostname or ""
    if (
        not hostname.endswith("xiaoyuzhoufm.com")
        and not is_douyin_url(source_url)
        and not is_xiaohongshu_url(source_url)
    ):
        return source_url, None

    try:
        parse_response = parse_media_source(source_url)
    except HTTPException:
        return source_url, None

    return parse_response.transcription_source_url or source_url, None
