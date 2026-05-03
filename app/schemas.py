from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
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


class ReservationCreate(BaseModel):
    game_id: int


class ReservationOut(BaseModel):
    id: int
    game_id: int
    reserved_at: datetime
    returned_at: Optional[datetime] = None
    game: BoardGameOut

    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    duration_rating: str  # 15 min, 30 min, 45 min, 60 min, more then 60 min
    rules_simplicity: int


class PopularGame(BaseModel):
    game_id: int
    name: str
    reservations_count: int
    demand_ratio: float  # reservations / total_quantity