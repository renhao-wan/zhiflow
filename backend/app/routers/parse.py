"""媒体解析路由。"""

import logging
import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.config import PARSE_RATE_LIMIT_PER_HOUR
from app.http_utils import enforce_rate_limit, normalize_public_video_url
from app.schemas import ParseRequest, ParseResponse
from app.services.library_service import (
    get_library_detail_by_source_url,
    upsert_library_item,
)
from app.services.media_source_service import parse_media_source
from app.services.xiaohongshu_service import is_xiaohongshu_url

router = APIRouter(prefix="/api/parse", tags=["parse"])

logger = logging.getLogger(__name__)


@router.post("", response_model=ParseResponse)
def parse_video(request: Request, parse_request: ParseRequest) -> ParseResponse:
    """
    校验真实解析入口，并返回媒体元数据解析结果。
    """
    video_url = normalize_public_video_url(parse_request.url)
    try:
        cached_detail = get_library_detail_by_source_url(video_url)
    except (sqlite3.Error, OSError, ValueError) as error:
        cached_detail = None
        logger.warning("library cache lookup failed: %s", error.__class__.__name__)

    if cached_detail is not None and not is_xiaohongshu_url(video_url):
        return cached_detail

    enforce_rate_limit(request, "parse", PARSE_RATE_LIMIT_PER_HOUR)
    parse_response = parse_media_source(video_url)
    if cached_detail is not None:
        parse_response = _merge_refreshed_xiaohongshu_detail(
            cached_detail,
            parse_response,
        )
    try:
        upsert_library_item(parse_response)
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning("library upsert failed: %s", error.__class__.__name__)

    return parse_response


def _merge_refreshed_xiaohongshu_detail(
    cached_detail: ParseResponse,
    refreshed_detail: ParseResponse,
) -> ParseResponse:
    """刷新平台元数据时保留用户已经生成的转写、总结和摘录。"""
    refreshed_author = refreshed_detail.video.author.strip()
    keep_cached_author = refreshed_author.lower() in {
        "",
        "unknown",
        "未知",
        "未知作者",
    }
    page_metadata_refreshed = bool(refreshed_detail.transcription_source_url)
    merged_video = refreshed_detail.video.model_copy(
        update={
            "author": (
                cached_detail.video.author
                if keep_cached_author
                else refreshed_detail.video.author
            ),
            "has_transcript": cached_detail.video.has_transcript,
            "media_type": (
                cached_detail.video.media_type or refreshed_detail.video.media_type
            ),
            "text_source_type": (
                cached_detail.video.text_source_type
                if cached_detail.video.has_transcript
                else refreshed_detail.video.text_source_type
            ),
            # 页面补取失败时 yt-dlp 可能再次给出 WB_PRV，不能覆盖已有封面。
            "thumbnail": (
                refreshed_detail.video.thumbnail
                if page_metadata_refreshed
                else cached_detail.video.thumbnail
            ),
        }
    )
    return refreshed_detail.model_copy(
        update={
            "video": merged_video,
            "transcript": cached_detail.transcript,
            "transcript_variants": cached_detail.transcript_variants,
            "active_transcript_variant": cached_detail.active_transcript_variant,
            "summary": cached_detail.summary,
            "mindmap_markdown": cached_detail.mindmap_markdown,
            "mindmap_meta": cached_detail.mindmap_meta,
            "note_draft": cached_detail.note_draft,
            "is_placeholder": cached_detail.is_placeholder,
            "library_summary_status": cached_detail.library_summary_status,
            "library_summary_model": cached_detail.library_summary_model,
        }
    )


def build_placeholder_parse_result(video_url: str) -> ParseResponse:
    """
    构造解析失败时的可解释返回。
    """
    return ParseResponse(
        source_url=video_url,
        is_placeholder=True,
        video={
            "video_id": "placeholder_parse_result",
            "platform": "placeholder",
            "url": video_url,
            "title": "媒体解析暂未完成",
            "author": "知流本地解析",
            "duration": 0,
            "thumbnail": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
            "has_transcript": False,
            "media_type": "media",
            "text_source_type": "content",
        },
        formats=[
            {
                "format_id": "placeholder-format",
                "ext": "mp4",
                "resolution": "待解析",
                "vcodec": "待接入",
                "acodec": "待接入",
                "filesize": None,
                "label": "真实格式待接入",
            }
        ],
        transcript={
            "segments": [
                {
                    "start": 0,
                    "end": 0,
                    "text": "当前链接已通过基础校验，但暂时没有取得可用媒体内容。",
                }
            ],
            "plain_text": "当前链接已通过基础校验，但暂时没有取得可用媒体内容。",
        },
        summary={
            "tldr": "当前链接暂时没有解析出可用媒体内容，请稍后重试或换一个公开链接。",
            "key_points": [
                "链接格式已通过基础校验。",
                "当前没有取得可用于总结的标题、内容文本或下载格式。",
                "拿到内容文本后，再生成结构化总结、摘录和导图。",
            ],
            "timeline": [],
            "structured_analysis_markdown": "## 当前状态\n### 链接已接收\n系统已完成基础校验。\n### 暂未取得内容\n请确认链接公开可访问，或稍后重新解析。",
            "takeaways": [
                "优先使用公开可访问、带标题和内容文本的媒体链接。",
                "平台临时限制访问时，可以稍后重试。",
            ],
        },
        mindmap_markdown="# 媒体解析\n## 当前状态\n### 链接已接收\n## 下一步\n### 重新解析公开可访问链接",
    )
