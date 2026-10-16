"""REST-эндпоинты каталога карт (только чтение)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import ActionCard, ActionDefinition, District, EventCard, Gang
from ..schemas import (ActionCardOut, ActionDefinitionOut, DistrictOut,
                       EventCardOut, GangOut)

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/districts", response_model=list[DistrictOut])
async def list_districts(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(District).order_by(District.id))
    return rows.scalars().all()


@router.get("/actions", response_model=list[ActionDefinitionOut])
async def list_actions(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(ActionDefinition).order_by(ActionDefinition.id))
    return rows.scalars().all()


@router.get("/action-cards", response_model=list[ActionCardOut])
async def list_action_cards(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(ActionCard).order_by(ActionCard.id))
    return rows.scalars().all()


@router.get("/events", response_model=list[EventCardOut])
async def list_events(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(EventCard).order_by(EventCard.id))
    return rows.scalars().all()


@router.get("/gangs", response_model=list[GangOut])
async def list_gangs(session: AsyncSession = Depends(get_session)):
    rows = await session.execute(select(Gang).order_by(Gang.id))
    return rows.scalars().all()