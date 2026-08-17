"""媒体下载路由。"""

import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.http_utils import normalize_public_video_url
from app.schemas import DownloadRequest, DownloadResponse
from app.services.bilibili_service import (
    download_bilibili_video_format,
    is_bilibili_url,
)
from app.services.douyin_service import download_douyin_video, is_douyin_url
from app.services.ytdlp_service import download_video_format

router = APIRouter(prefix="/api", tags=["download"])

logger = logging.getLogger(__name__)


def _remove_completed_download(file_path: Path) -> None:
    """浏览器接收完文件后删除后端生成的临时下载文件。"""
    try:
        file_path.unlink(missing_ok=True)
    except OSError as error:
        logger.warning(
            "failed to remove completed browser download: %s",
            error.__class__.__name__,
        )


def _prepare_video_download(download_request: DownloadRequest) -> DownloadResponse:
    """复用各平台下载实现，返回后端已准备好的文件信息。"""
    video_url = normalize_public_video_url(download_request.url)
    if is_bilibili_url(video_url):
        return download_bilibili_video_format(
            source_url=video_url,
            format_id=download_request.format_id,
            merge_with_audio=download_request.merge_with_audio,
        )

    if is_douyin_url(video_url):
        return download_douyin_video(video_url)

    return download_video_format(
        video_url=video_url,
        format_id=download_request.format_id,
        merge_with_audio=download_request.merge_with_audio,
    )


@router.post("/download", response_model=DownloadResponse)
def download_video_legacy(download_request: DownloadRequest) -> DownloadResponse:
    """保留旧 JSON 协议，避免已打开页面把媒体二进制误当作 JSON。"""
    return _prepare_video_download(download_request)


@router.post("/download/file", response_class=FileResponse)
def download_video_file(download_request: DownloadRequest) -> FileResponse:
    """
    准备用户选择的公开视频格式，并作为浏览器附件下载返回。
    """
    download_result = _prepare_video_download(download_request)
    download_path = Path(download_result.file_path)
    return FileResponse(
        path=download_path,
        filename=download_result.filename,
        media_type="application/octet-stream",
        background=BackgroundTask(_remove_completed_download, download_path),
    )
