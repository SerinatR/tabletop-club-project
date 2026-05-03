"""Module controlling games manipulations"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud

router = APIRouter()


@router.post("/", response_model=schemas.BoardGameOut)
def create_game(game: schemas.BoardGameCreate, db: Session = Depends(get_db)):
    """Admin endpoint for creating new game in database"""
    return crud.create_game(db, game)


@router.get("/", response_model=list[schemas.BoardGameOut])
def read_games(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Endpoint for showing all games in database"""
    return crud.get_games(db, skip, limit)


@router.get("/{name}", response_model=schemas.BoardGameOut)
def read_game(
        name: str,
        db: Session = Depends(get_db)
):
    """Endpoint to see data of the particular game"""
    game = crud.get_game(db, name)
    if not game:
        raise HTTPException(404, "Game not found")
    return game


@router.put("/{name}", response_model=schemas.BoardGameOut)
def update_game(
        name: str,
        game_update: schemas.BoardGameCreate,
        db: Session = Depends(get_db)
):
    """Admin endpoint to update game details in database"""
    return crud.update_game(db, name, game_update)


@router.delete("/{name}")
def delete_game(
        name: str,
        db: Session = Depends(get_db)
):
    """Admin endpoint to delete a game from database"""
    return crud.delete_game(db, name)
