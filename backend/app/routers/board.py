"""REST-эндпоинты игрового поля (раскладки и рёбра гексов)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import BoardLayout, HexEdge
from ..schemas import BoardDetailOut, BoardLayoutOut, HexEdgeOut

router = APIRouter(prefix="/api/board", tags=["board"])


@router.get("/layouts", response_model=list[BoardLayoutOut])
async def list_layouts(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(BoardLayout).order_by(BoardLayout.player_count))
    return rows.scalars().all()


@router.get("/layout/{player_count}", response_model=BoardDetailOut)
async def get_layout(player_count: int, session: AsyncSession = Depends(get_session)):
    layout = (await session.execute(
        select(BoardLayout).where(BoardLayout.player_count == player_count)
    )).scalar_one_or_none()
    if layout is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Layout not found")

    edges = (await session.execute(
        select(HexEdge).where(HexEdge.player_count == player_count).order_by(HexEdge.id)
    )).scalars().all()

    return BoardDetailOut(
        player_count=layout.player_count,
        districts=layout.districts,
        edges=[HexEdgeOut.model_validate(e) for e in edges],
    )