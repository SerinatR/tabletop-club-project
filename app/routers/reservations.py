from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud, models
from ..dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=schemas.ReservationOut)
def reserve_game(res: schemas.ReservationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.create_reservation(db, current_user.id, res.game_id)


@router.post("/return")
def return_current_game(rating: schemas.RatingCreate = None,
                        db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):

    active_reservation = db.query(models.Reservation).filter(
        models.Reservation.user_id == current_user.id,
        models.Reservation.returned_at.is_(None)
    ).first()

    if not active_reservation:
        raise HTTPException(status_code=400, detail="У вас нет активной резервации")

    return crud.return_game(db, active_reservation.id, rating)


@router.post("/{reservation_id}/return")
def return_game(reservation_id: int, rating: schemas.RatingCreate = None, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    return crud.return_game(db, reservation_id, rating)
