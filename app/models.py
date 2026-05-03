from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class Role(str, enum.Enum):
    USER = 'user'
    ADMIN = 'admin'


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default=Role.USER.value)

    reservations = relationship("Reservation", back_populates="user")


class Category(str, enum.Enum):
    ECONOMIC = "economic"
    WARGAME = "wargame"
    COOP = "coop"
    PARTY = "party"
    STRATEGY = "strategy"
    OTHER = "other"


class BoardGame(Base):
    __tablename__ = "boardgames"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    min_players = Column(Integer)
    max_players = Column(Integer)
    duration = Column(Integer)  # session duration in minutes
    category = Column(SQLEnum(Category))
    description = Column(String)
    total_quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)

    reservations = relationship("Reservation", back_populates="game")


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("boardgames.id"))
    reserved_at = Column(DateTime(timezone=True), server_default=func.now())
    returned_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="reservations")
    game = relationship("BoardGame", back_populates="reservations")


class DurationRating(str, enum.Enum):
    MIN_15 = "15 min"
    MIN_30 = "30 min"
    MIN_45 = "45 min"
    MIN_60 = "60 min"
    MORE_60 = "more than 60 min"


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), unique=True)
    duration_rating = Column(SQLEnum(DurationRating))  # 15 min, 30 min, 45 min...
    rules_simplicity = Column(Integer)  # score from 1 to 5
