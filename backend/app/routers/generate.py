"""AI 内容生成路由：结构化总结与问答。"""

import logging
import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.config import (
    QA_RATE_LIMIT_PER_HOUR,
    SUMMARY_RATE_LIMIT_PER_HOUR,
)
from app.http_utils import enforce_rate_limit
from app.schemas import QaRequest, QaResponse, SummarizeRequest, SummarizeResponse
from app.services.deepseek_client import DeepSeekOutputTruncatedError
from app.services.library_service import (
    get_library_detail_by_source_url,
    update_summary_for_source_url,
)
from app.services.qa_service import answer_question
from app.services.summarize_service import summarize_transcript

router = APIRouter(prefix="/api", tags=["generate"])

logger = logging.getLogger(__name__)


def _raise_truncated_error() -> HTTPException:
    return HTTPException(
        status_code=502,
        detail={
            "success": False,
            "error_code": "AI_OUTPUT_TRUNCATED",
            "message": (
                "AI 输出达到长度限制，结果未完整生成。"
                "请稍后重试，或提高对应的最大输出长度后再试。"
            ),
        },
    )


def _hydrate_summarize_request_from_library(
    summarize_request: SummarizeRequest,
) -> SummarizeRequest:
    """从本地历史补回原始 shownotes 和已提取上下文，不重复调用 AI。"""
    if not summarize_request.source_url:
        return summarize_request

    try:
        detail = get_library_detail_by_source_url(summarize_request.source_url)
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning(
            "library shownotes lookup failed for summary: %s",
            error.__class__.__name__,
        )
        return summarize_request

    if detail is None:
        return summarize_request

    updates: dict[str, object] = {}
    if detail.shownotes_plain_text:
        updates["shownotes_plain_text"] = detail.shownotes_plain_text
    if detail.shownotes_context is not None:
        updates["shownotes_context"] = detail.shownotes_context
    return summarize_request.model_copy(update=updates) if updates else summarize_request


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_video(
    request: Request,
    summarize_request: SummarizeRequest,
) -> SummarizeResponse:
    """
    基于现有内容文本生成结构化总结。
    """
    if not summarize_request.transcript_plain_text.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "TRANSCRIPT_EMPTY",
                "message": "没有可用于总结的内容文本。",
            },
        )

    if (summarize_request.text_source_type or "").strip().lower() == "shownotes":
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "FULL_TRANSCRIPT_REQUIRED",
                "message": "当前只有 shownotes 原文，请先生成完整逐字稿，再生成总结和导图。",
            },
        )

    enforce_rate_limit(request, "summarize", SUMMARY_RATE_LIMIT_PER_HOUR)
    enriched_request = _hydrate_summarize_request_from_library(summarize_request)
    try:
        summarize_response = summarize_transcript(enriched_request)
    except DeepSeekOutputTruncatedError as error:
        logger.warning("AI summary output truncated")
        raise _raise_truncated_error() from error
    try:
        update_summary_for_source_url(
            enriched_request.source_url,
            summarize_response,
        )
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning(
            "library summary update failed: %s",
            error.__class__.__name__,
        )

    return summarize_response


@router.post("/qa", response_model=QaResponse)
def answer_media_question(request: Request, qa_request: QaRequest) -> QaResponse:
    """
    基于当前内容文本回答用户问题。
    """
    if not qa_request.question.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "QUESTION_EMPTY",
                "message": "请输入要询问的问题。",
            },
        )

    if not qa_request.transcript_plain_text.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "TRANSCRIPT_EMPTY",
                "message": "没有可用于问答的内容文本。",
            },
        )

    if (qa_request.text_source_type or "").strip().lower() == "shownotes":
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_code": "FULL_TRANSCRIPT_REQUIRED",
                "message": "当前只有 shownotes 原文，请先生成完整逐字稿，再进行内容问答。",
            },
        )

    enforce_rate_limit(request, "qa", QA_RATE_LIMIT_PER_HOUR)
    try:
        return answer_question(qa_request)
    except DeepSeekOutputTruncatedError as error:
        logger.warning("AI qa output truncated")
        raise _raise_truncated_error() from error
