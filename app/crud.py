from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from . import models, schemas
from .auth import get_password_hash


def create_user(db: Session, user: schemas.UserCreate):
    hashed = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_game(db: Session, game: schemas.BoardGameCreate):
    db_game = models.BoardGame(**game.dict(), available_quantity=game.total_quantity)
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_games(db: Session, skip=0, limit=100):
    return db.query(models.BoardGame).offset(skip).limit(limit).all()


def get_game(db: Session, game_id: int):
    return db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()


def create_reservation(db: Session, user_id: int, game_id: int):
    active = db.query(models.Reservation).filter(
        models.Reservation.user_id == user_id,
        models.Reservation.returned_at.is_(None)
    ).first()
    if active:
        raise HTTPException(400, "У вас уже есть активная резервация. Верните предыдущую игру.")

    game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if not game or game.available_quantity < 1:
        raise HTTPException(400, "Игра недоступна.")

    reservation = models.Reservation(user_id=user_id, game_id=game_id)
    game.available_quantity -= 1
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def return_game(db: Session, reservation_id: int, rating: schemas.RatingCreate = None):
    res = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
    if not res or res.returned_at:
        raise HTTPException(400, "Резервация не найдена или уже возвращена.")

    res.returned_at = func.now()
    res.game.available_quantity += 1

    if rating:
        rating_obj = models.Rating(
            reservation_id=reservation_id,
            duration_rating=rating.duration_rating,
            rules_simplicity=rating.rules_simplicity
        )
        db.add(rating_obj)

    db.commit()
    db.refresh(res)
    return res


def get_popular_games(db: Session, limit=10):
    stats = db.query(
        models.BoardGame.id,
        models.BoardGame.name,
        func.count(models.Reservation.id).label("res_count"),
        (func.count(models.Reservation.id) * 1.0 / models.BoardGame.total_quantity).label("demand")
    ).join(models.Reservation, models.Reservation.game_id == models.BoardGame.id)\
     .group_by(models.BoardGame.id)\
     .order_by(func.count(models.Reservation.id).desc())\
     .limit(limit).all()

    return \
        [{"game_id": r[0], "name": r[1], "reservations_count": r[2], "demand_ratio": round(float(r[3]), 2)}
            for r in stats]
