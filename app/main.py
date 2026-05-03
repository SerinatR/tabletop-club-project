from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .routers import games, reservations, analytics
from . import schemas, crud, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Board Game Club API")

app.include_router(games.router, prefix="/games", tags=["games"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


@app.post("/token", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(401, "Неверные данные")
    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
