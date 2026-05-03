from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=schemas.ReservationOut)
def reserve_game(res: schemas.ReservationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return crud.create_reservation(db, current_user.id, res.game_id)


@router.post("/{reservation_id}/return")
def return_game(reservation_id: int, rating: schemas.RatingCreate = None, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    return crud.return_game(db, reservation_id, rating)
