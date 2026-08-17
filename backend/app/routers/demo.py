"""内置推荐内容路由。"""

from typing import Any

from fastapi import APIRouter, HTTPException, Response

from app.demo_data import get_demo_by_id, load_demo_seed
from app.routers.media import proxy_public_image
from app.schemas import DemoItem, DemoListResponse, ParseResponse
from app.services.demo_cover_service import resolve_demo_cover_url

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/demo", response_model=DemoListResponse)
def list_demos() -> DemoListResponse:
    """
    返回内置的推荐内容列表。
    """
    demos = [
        DemoItem(
            demo_id=demo["demo_id"],
            title=demo["title"],
            description=demo["description"],
            thumbnail=f"/api/demo/{demo['demo_id']}/cover",
        )
        for demo in load_demo_seed()
    ]
    return DemoListResponse(demos=demos)


@router.get("/demo/{demo_id}/cover")
def get_demo_cover(demo_id: str) -> Response:
    """返回推荐内容当前可用的媒体源封面。"""
    demo = get_demo_by_id(demo_id)
    if demo is None:
        raise HTTPException(status_code=404, detail="未找到该推荐内容。")

    cover_url = resolve_demo_cover_url(demo)
    if not cover_url:
        raise HTTPException(status_code=404, detail="该推荐内容暂时没有可用封面。")

    return proxy_public_image(url=cover_url)


@router.get("/demo/{demo_id}", response_model=ParseResponse)
def get_demo_detail(demo_id: str) -> dict[str, Any]:
    """
    返回推荐内容的精简公开数据。
    """
    demo = get_demo_by_id(demo_id)
    if demo is None:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error_code": "DEMO_NOT_FOUND",
                "message": "未找到该推荐内容。",
            },
        )

    response = dict(demo)
    video = dict(response["video"])
    video["thumbnail"] = f"/api/demo/{demo_id}/cover"
    response["video"] = video
    response["thumbnail"] = f"/api/demo/{demo_id}/cover"

    return response
