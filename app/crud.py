"""Module for CRUD operations"""
# pylint: disable=not-callable

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from . import models, schemas
from .auth import get_password_hash


def create_user(db: Session, user: schemas.UserCreate, role: str = "user"):
    """Creates new user"""
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(
            status_code=400,
            detail="Имя пользователя уже занято"
        )

    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(
            status_code=400,
            detail="Данная электронная почта уже занята"
        )

    hashed = get_password_hash(user.password)

    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed,
        full_name=user.full_name,
        role=role
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Ошибка при создании пользователя. Возможно, email или username уже заняты."
        ) from exc


def create_game(db: Session, game: schemas.BoardGameCreate):
    """Creates new game in database"""
    db_game = models.BoardGame(**game.dict(), available_quantity=game.total_quantity)
    try:
        db.add(db_game)
        db.commit()
        db.refresh(db_game)
        return db_game
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Игра с таким названием уже существует"
        ) from exc


def get_games(db: Session, skip=0, limit=100):
    """Shows all games in database"""
    return db.query(models.BoardGame).offset(skip).limit(limit).all()


def get_game(db: Session, game_name: str):
    """Shows particular game in database"""
    return db.query(models.BoardGame).filter(models.BoardGame.name == game_name).first()


def create_reservation(db: Session, user_id: int, game_name: str):
    """Reserves copy of a game for user"""
    active = db.query(models.Reservation).filter(
        models.Reservation.user_id == user_id,
        models.Reservation.returned_at.is_(None)
    ).first()
    if active:
        raise HTTPException(400, "У вас уже есть активная резервация. Верните предыдущую игру.")

    game = db.query(models.BoardGame).filter(models.BoardGame.name == game_name).first()
    if not game or game.available_quantity < 1:
        raise HTTPException(400, "Игра недоступна.")

    reservation = models.Reservation(user_id=user_id, game_id=game.id)
    game.available_quantity -= 1
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def return_game(db: Session, reservation_id: int, rating: schemas.RatingCreate = None):
    """Frees a game from the user"""
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
    """Calculates most demanded games"""
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
        [{"game_id": r[0], "name": r[1], "reservations_count": r[2],
          "demand_ratio": round(float(r[3]), 2)}
            for r in stats]


def update_game(db: Session, name: str, game_update: schemas.BoardGameCreate):
    """Functionality to update existing game"""
    game = db.query(models.BoardGame).filter(models.BoardGame.name == name).first()
    if not game:
        raise HTTPException(404, "Такой игры нет")

    for key, value in game_update.dict().items():
        setattr(game, key, value)
    db.commit()
    db.refresh(game)
    return game


def delete_game(db: Session, name: str):
    """Game deletion"""
    game = db.query(models.BoardGame).filter(models.BoardGame.name == name).first()
    if not game:
        raise HTTPException(404, "Такой игры нет")
    db.delete(game)
    db.commit()
    return {"detail": "Игра успешно удалена"}


def get_user_reservation_stats(db: Session):
    """Shows games reservation history of the user"""
    stats = db.query(
        models.User.username,
        models.User.full_name,
        func.count(models.Reservation.id).label("total_res"),
    ).join(models.Reservation, models.Reservation.user_id == models.User.id)\
     .group_by(models.User.id)\
     .having(func.count(models.Reservation.id) > 0)\
     .order_by(func.count(models.Reservation.id).desc()).all()

    result = []
    for user in stats:
        games = db.query(
            models.BoardGame.name,
            func.count(models.Reservation.id).label("count")
        ).join(models.Reservation, models.Reservation.game_id == models.BoardGame.id)\
         .filter(models.Reservation.user_id ==
                 db.query(models.User.id).filter(models.User.username == user.username).scalar())\
         .group_by(models.BoardGame.name)\
         .all()

        game_list = [{"game_name": g[0], "reservations_count": g[1]} for g in games]

        result.append({
            "username": user.username,
            "full_name": user.full_name,
            "total_reservations": user.total_res,
            "games": game_list
        })

    return result


def get_purchase_suggestions(db: Session, limit: int = 3):
    """Shows top demanded games for potential buying"""
    suggestions = db.query(
        models.BoardGame.id,
        models.BoardGame.name,
        func.count(models.Reservation.id).label("res_count"),
        models.BoardGame.available_quantity,
        (func.count(models.Reservation.id) / models.BoardGame.total_quantity).label("demand")
    ).join(models.Reservation, models.Reservation.game_id == models.BoardGame.id, isouter=True)\
     .group_by(models.BoardGame.id)\
     .order_by(func.count(models.Reservation.id).desc(), models.BoardGame.available_quantity.asc())\
     .limit(limit).all()

    result = []
    for s in suggestions:
        result.append({
            "game_id": s[0],
            "name": s[1],
            "reservations_count": s[2] or 0,
            "available_quantity": s[3],
            "demand_ratio": round(float(s[4] or 0), 2),
            "recommendation": "Рекомендуется закупить" if (s[3] or 0) <= 1 and (s[2] or 0) > 5
            else "Достаточное количество"
        })
    return result


def get_user_recommendations(db: Session, user_id: int, limit: int = 5):
    """Recommends new games to a user"""
    preferred_categories = db.query(models.BoardGame.category)\
        .join(models.Reservation, models.Reservation.game_id == models.BoardGame.id)\
        .filter(models.Reservation.user_id == user_id)\
        .distinct().all()

    if not preferred_categories:
        return get_popular_games(db, limit)

    recommendations = db.query(
        models.BoardGame.id,
        models.BoardGame.name,
        models.BoardGame.category,
        func.count(models.Reservation.id).label("popularity")
    ).filter(
        models.BoardGame.category.in_([cat[0] for cat in preferred_categories]),
        ~models.BoardGame.id.in_(
            db.query(models.Reservation.game_id).filter(models.Reservation.user_id == user_id)
        )
    ).outerjoin(models.Reservation, models.Reservation.game_id == models.BoardGame.id)\
     .group_by(models.BoardGame.id)\
     .order_by(func.count(models.Reservation.id).desc())\
     .limit(limit).all()

    return [
        {
            "game_id": r[0],
            "name": r[1],
            "category": r[2],
            "reason": f"Популярная игра в категории {r[2]}, которую вы ещё не пробовали"
        } for r in recommendations
    ]
