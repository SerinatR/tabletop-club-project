from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime
from typing import Optional, List, Literal
from .models import Category


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class BoardGameBase(BaseModel):
    name: str
    min_players: int
    max_players: int
    duration: int
    category: Category
    description: str
    total_quantity: int = 1


class BoardGameCreate(BoardGameBase):
    pass


class BoardGameOut(BoardGameBase):
    id: int
    available_quantity: int

    class Config:
        from_attributes = True


class GameActionByName(BaseModel):
    name: str


class ReservationCreate(BaseModel):
    game_name: str


class ReservationOut(BaseModel):
    id: int
    game_id: int
    reserved_at: datetime
    returned_at: Optional[datetime] = None
    game: BoardGameOut

    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    duration_rating: Literal[
        "15 min",
        "30 min",
        "45 min",
        "60 min",
        "more than 60 min"
    ] = Field(..., description="Длительность партии")

    rules_simplicity: int = Field(..., ge=1, le=5, description="Простота правил от 1 до 5")

    @field_validator('rules_simplicity')
    @classmethod
    def validate_rules(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError('Простота правил должна быть от 1 до 5')
        return v


class PopularGame(BaseModel):
    game_id: int
    name: str
    reservations_count: int
    demand_ratio: float  # reservations / total_quantity