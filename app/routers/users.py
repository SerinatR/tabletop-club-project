from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models
from ..dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(current_user = Depends(get_current_user)):
    return current_user


@router.get("/my-reservations", response_model=list[schemas.ReservationOut])
def get_my_reservations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    reservations = db.query(models.Reservation)\
        .filter(models.Reservation.user_id == current_user.id)\
        .order_by(models.Reservation.reserved_at.desc()).all()
    return reservations
