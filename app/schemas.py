"""Module for app schemas"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr
from .models import Category


class UserCreate(BaseModel):
    """Class for user creation"""
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserOut(BaseModel):
    """Class for user loging out"""
    id: int
    username: str
    email: str
    full_name: str
    role: str

    class Config:
        """Configuration class"""
        from_attributes = True


class Token(BaseModel):
    """Token class"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data class"""
    username: Optional[str] = None


class BoardGameBase(BaseModel):
    """Class for the game"""
    name: str
    min_players: int
    max_players: int
    duration: int
    category: Category
    description: str
    total_quantity: int = 1


class BoardGameCreate(BoardGameBase):
    """Class for game creation"""


class BoardGameOut(BoardGameBase):
    """Class for exiting games, currently placeholder"""
    id: int
    available_quantity: int

    class Config:
        """Configuration class"""
        from_attributes = True


class GameActionByName(BaseModel):
    """Class for actions with games based on their name"""
    name: str


class ReservationCreate(BaseModel):
    """Class for reserving a game"""
    game_name: str


class ReservationOut(BaseModel):
    """Class for returned game"""
    id: int
    game_id: int
    reserved_at: datetime
    returned_at: Optional[datetime] = None
    game: BoardGameOut

    class Config:
        """Configuration class"""
        from_attributes = True


class RatingCreate(BaseModel):
    """Class for leaving rating for returned game"""
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
        """Class to check valid rating input"""
        if v < 1 or v > 5:
            raise ValueError('Простота правил должна быть от 1 до 5')
        return v


class PopularGame(BaseModel):
    """Class for defining games in high demand"""
    game_id: int
    name: str
    reservations_count: int
    demand_ratio: float  # reservations / total_quantity


class UserReservationStats(BaseModel):
    """Class for user reservation history"""
    username: str
    full_name: str
    total_reservations: int
    games: list[dict]   # список игр с количеством


class UserReservationsAnalytics(BaseModel):
    """Class to see analytics of games reservations"""
    users: list[UserReservationStats]


class PurchaseSuggestion(BaseModel):
    """Class to define whether to recommend a game for purchase"""
    game_id: int
    name: str
    reservations_count: int
    available_quantity: int
    demand_ratio: float
    recommendation: str


class GameRecommendation(BaseModel):
    """Class to recommend new games for a user"""
    game_id: int
    name: str
    category: str
    reason: str
