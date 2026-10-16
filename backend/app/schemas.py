"""Pydantic-схемы ответов каталога, поля и запросов."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DistrictOut(ORMModel):
    id: int
    name: str
    type_key: str
    build_cost: int
    income: int
    ability: dict | None = None


class ActionDefinitionOut(ORMModel):
    id: int
    key: str
    kind: str
    title: str
    text: str
    options: list | None = None


class ActionCardOut(ORMModel):
    id: int
    player_group: str
    standard_key: str
    situational_key: str
    draft: bool


class EventCardOut(ORMModel):
    id: int
    slug: str
    title: str
    text: str
    player_group: str
    draft: bool


class GangOut(ORMModel):
    id: int
    slug: str
    name: str
    ability_text: str | None = None
    draft: bool


class BoardLayoutOut(ORMModel):
    player_count: int
    districts: list


class HexEdgeOut(ORMModel):
    id: int
    player_count: int
    a: int
    b: int
    kind: str
    draft: bool


class BoardDetailOut(BaseModel):
    player_count: int
    districts: list
    edges: list[HexEdgeOut]


class CreateGameRequest(BaseModel):
    player_count: int = Field(ge=2, le=4)
    seed: int = 0

class CreateRoomRequest(BaseModel):
    player_count: int = Field(ge=2, le=4)


class RoomOut(BaseModel):
    code: str
    player_count: int
    status: str
    seats_taken: list[bool]
    game_id: str | None = None


class CreateRoomResponse(BaseModel):
    code: str
    token: str
    seat: int
    player_count: int


class JoinRoomResponse(BaseModel):
    code: str
    token: str
    seat: int


class StartRoomResponse(BaseModel):
    game_id: str


class MoveOut(BaseModel):
    id: int
    version: int
    seat: int
    command: dict
    summary: str
    created_at: datetime
