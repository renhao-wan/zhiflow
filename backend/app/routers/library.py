"""本地内容库与导出路由。"""

import logging
import sqlite3
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.http_utils import normalize_public_video_url
from app.schemas import (
    LibraryClearResponse,
    LibraryDeleteResponse,
    LibraryListResponse,
    LibraryStatsResponse,
    NoteDraft,
    NoteDraftUpdateRequest,
    NoteDraftUpdateResponse,
    ObsidianNoteExportRequest,
    ObsidianNoteExportResponse,
    ParseResponse,
)
from app.services.library_service import (
    clear_library_items,
    delete_library_item,
    get_library_detail,
    list_recent_library_items,
    get_library_stats,
    update_note_draft_for_source_url,
)
from app.services.obsidian_export_service import (
    ObsidianExportError,
    export_obsidian_note,
)

router = APIRouter(prefix="/api", tags=["library"])

logger = logging.getLogger(__name__)


@router.get("/library/recent", response_model=LibraryListResponse)
def list_recent_library(
    limit: int = Query(default=8, ge=1, le=50),
    filter: Literal["all", "ready", "summarized", "noTranscript"] = Query(
        default="all"
    ),
) -> LibraryListResponse:
    """
    返回最近解析过的媒体记录。
    """
    return LibraryListResponse(
        items=list_recent_library_items(limit=limit, library_filter=filter)
    )


@router.get("/library/stats", response_model=LibraryStatsResponse)
def get_local_library_stats() -> LibraryStatsResponse:
    """
    返回本地内容库统计概览。
    """
    return get_library_stats()


@router.put("/library/note-draft", response_model=NoteDraftUpdateResponse)
def update_library_note_draft(
    note_draft_request: NoteDraftUpdateRequest,
) -> NoteDraftUpdateResponse:
    """
    保存当前媒体的摘录草稿到本地历史记录。
    """
    source_url = normalize_public_video_url(note_draft_request.source_url)
    note_draft = NoteDraft(
        highlights=note_draft_request.highlights,
        updated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    try:
        updated_note_draft = update_note_draft_for_source_url(source_url, note_draft)
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning(
            "library note draft update failed: %s",
            error.__class__.__name__,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "NOTE_DRAFT_SAVE_FAILED",
                "message": "摘录草稿保存失败，请稍后重试。",
            },
        ) from error

    if updated_note_draft is None:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error_code": "LIBRARY_ITEM_NOT_FOUND",
                "message": "没有找到可保存摘录的本地历史记录。",
            },
        )

    return NoteDraftUpdateResponse(note_draft=updated_note_draft)


@router.post("/exports/obsidian-note", response_model=ObsidianNoteExportResponse)
def export_library_obsidian_note(
    export_request: ObsidianNoteExportRequest,
) -> ObsidianNoteExportResponse:
    """
    生成或写入 Obsidian Markdown 笔记。
    """
    source_url = normalize_public_video_url(export_request.source_url)
    try:
        return export_obsidian_note(
            source_url=source_url,
            include_full_text=export_request.include_full_text,
        )
    except ObsidianExportError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "success": False,
                "error_code": error.error_code,
                "message": error.message,
            },
        ) from error
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.warning(
            "obsidian note export failed: %s",
            error.__class__.__name__,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "OBSIDIAN_EXPORT_FAILED",
                "message": "Obsidian Markdown 导出失败，请稍后重试。",
            },
        ) from error


@router.delete("/library", response_model=LibraryClearResponse)
def clear_local_library() -> LibraryClearResponse:
    """
    清空本地内容库历史记录。
    """
    return LibraryClearResponse(deleted_count=clear_library_items())


@router.get("/library/{video_id}", response_model=ParseResponse)
def get_library_item(video_id: str) -> ParseResponse:
    """
    返回本地内容库中的完整工作台数据。
    """
    detail = get_library_detail(video_id)
    if detail is None:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error_code": "LIBRARY_ITEM_NOT_FOUND",
                "message": "未找到该历史记录。",
            },
        )

    return detail


@router.delete("/library/{video_id}", response_model=LibraryDeleteResponse)
def delete_library_history_item(video_id: str) -> LibraryDeleteResponse:
    """
    删除本地内容库中的单条历史记录。
    """
    deleted = delete_library_item(video_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error_code": "LIBRARY_ITEM_NOT_FOUND",
                "message": "未找到该历史记录。",
            },
        )

    return LibraryDeleteResponse(deleted_video_id=video_id)
