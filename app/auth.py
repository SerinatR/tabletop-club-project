"""Module providing authentication capabilities"""

from datetime import datetime, timedelta
from jose import jwt
import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models


SECRET_KEY = "87^A&D*gtdg6TD7gd*T^sa_8GI87@O*SGfagdUS_AIBFIUdof8H(*fu3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def get_password_hash(password: str) -> str:
    """Password hashing"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checking password correctness"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_user(db: Session, username: str):
    """Pulls the user by their name"""
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    """Login function"""
    user = get_user(db, username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Такого пользователя не существует"
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверный пароль"
        )
    return user


def create_access_token(data: dict):
    """Creates access tokens for successful logins"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
