"""Module for analytics endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..dependencies import get_current_user, get_current_admin_user

router = APIRouter()


@router.get("/popular-games", response_model=list[schemas.PopularGame])
def popular_games(
        limit: int = 10,
        db: Session = Depends(get_db)
):
    """Endpoint to show most demanded games"""
    return crud.get_popular_games(db, limit)


@router.get("/user-reservations", response_model=dict)
def user_reservation_stats(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_admin_user)
):
    """Endpoint to show all users reservations history"""
    stats = crud.get_user_reservation_stats(db)
    return {"users": stats}


@router.get("/purchase-suggestions", response_model=list[schemas.PurchaseSuggestion])
def purchase_suggestions(
        limit: int = 3,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_admin_user)
):
    """Endpoint for suggesting potential most profitable games to buy"""
    return crud.get_purchase_suggestions(db, limit)


@router.get("/recommendations", response_model=list[schemas.GameRecommendation])
def user_recommendations(
        limit: int = 5,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    """Endpoint to recommend user new games to try"""
    return crud.get_user_recommendations(db, current_user.id, limit)
