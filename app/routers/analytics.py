from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud

router = APIRouter()


@router.get("/popular-games", response_model=list[schemas.PopularGame])
def popular_games(limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_popular_games(db, limit)
