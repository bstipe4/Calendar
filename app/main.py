import datetime

from fastapi import Depends, FastAPI, File, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import auth, crud, dependencies, schemas
from .services import calendar

app = FastAPI()


@app.post("/register/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(dependencies.get_db),
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.username},
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/import-calendar", status_code=status.HTTP_201_CREATED)
def import_calendar_from_file(
    file: bytes = File(...),
    db: Session = Depends(dependencies.get_db),
    current_user: schemas.User = Depends(dependencies.get_current_user),
):

    if not file:
        raise HTTPException(
            detail="No file attached", status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        calendar.import_calendar_from_file(db, current_user.id, file)
    except ValidationError:
        raise HTTPException(
            detail="Invalid ICS file", status_code=status.HTTP_400_BAD_REQUEST
        )

    except Exception:
        raise HTTPException(
            detail="Server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return {"message": "success"}


@app.post("/import-from-url", status_code=status.HTTP_201_CREATED)
def import_calendar_from_url(
    url: schemas.CalendarInputUrl,
    db: Session = Depends(dependencies.get_db),
    current_user: schemas.User = Depends(dependencies.get_current_user),
):

    try:
        calendar.import_calendar_from_url(db, current_user.id, url.url)
    except ValidationError:
        raise HTTPException(
            detail="Invalid ICS file", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        raise HTTPException(
            detail="Server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return {"message": "success"}


@app.get("/export/{apartment_id}", response_class=FileResponse)
def export_apartment_calendar(
    apartment_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: schemas.User = Depends(dependencies.get_current_user),
):

    apartment = crud.get_apartment_by_id(db, current_user.id, apartment_id)
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apartment not found",
        )

    calendar_data = calendar.generate_apartment_calendar(db, apartment_id)
    return Response(
        content=calendar_data,
        media_type="text/calendar",
        headers={"content-type": "text/calendar"},
    )


@app.get("/calendars")
def get_cleaning_dates(
    date_from: datetime.date,
    date_to: datetime.date,
    db: Session = Depends(dependencies.get_db),
    current_user: schemas.User = Depends(dependencies.get_current_user),
):

    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dates",
        )

    calendar_data = calendar.get_calendar_with_proposed_cleaning_days(
        db, current_user.id, date_from, date_to
    )

    return calendar_data
