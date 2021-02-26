from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth
from app.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)
):
    user = auth.get_user_from_token(db, token)
    if user is None:
        raise auth.CREDENTIALS_EXCEPTION
    return user
