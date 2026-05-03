from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..dependencies import get_current_user, get_current_admin_user

router = APIRouter()


@router.post("/", response_model=schemas.BoardGameOut)
def create_game(game: schemas.BoardGameCreate, db: Session = Depends(get_db),
                current_user = Depends(get_current_admin_user)):
    return crud.create_game(db, game)


@router.get("/", response_model=list[schemas.BoardGameOut])
def read_games(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_games(db, skip, limit)


@router.get("/{game_id}", response_model=schemas.BoardGameOut)
def read_game(game_id: int, db: Session = Depends(get_db)):
    game = crud.get_game(db, game_id)
    if not game:
        raise HTTPException(404, "Game not found")
    return game
