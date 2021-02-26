import urllib
from datetime import timedelta
from typing import List
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
from pydantic import ValidationError
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, Response, Query
from icalendar import Calendar, Event

from . import crud, schemas, auth, utils, dependencies
from .auth import ACCESS_TOKEN_EXPIRE_MINUTES


app = FastAPI()


@app.post("/register/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(dependencies.get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(dependencies.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/import-calendar", status_code=status.HTTP_201_CREATED)
def import_calendar_from_file(file: bytes = File(...), db: Session = Depends(dependencies.get_db), current_user: schemas.User = Depends(dependencies.get_current_user)):

    c = Calendar.from_ical(file)
    apartment_id = c.get('prodid')

    events = []
    try:
        for event in c.subcomponents:
            item = schemas.EventCreate(
                start_date=event.get("dtstart").dt,
                end_date=event.get("dtend").dt,
                id=event.get("uid"),
                guest=event.get("summary"),
                apartment_id=apartment_id,
            )
            events.append(item)
    except ValidationError:
        raise HTTPException(detail="Invalid ICS file", status_code=status.HTTP_400_BAD_REQUEST)

    try:
        _, created = crud.get_or_create_apartment(db, current_user.id, apartment_id, commit=False)
        if not created:
            crud.delete_apartment_events(db, apartment_id)

        crud.create_events(db, events, commit=False)

        # end transaction
        db.commit()
    except Exception as ex:
        raise HTTPException(detail="Server error", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {"message": "success"}


@app.post("/import-from-url", status_code=status.HTTP_201_CREATED)
def import_calendar_from_url(url: schemas.CalendarInputUrl,  db: Session = Depends(dependencies.get_db)):
    file = urllib.request.urlopen(url)
    c = Calendar.from_ical(file.read().decode("utf-8"))
    print(c)
    # apartment_id = c.get('prodid')
    # events = []
    # # TODO filea validacija ode gori u funkciji
    # for event in c.subcomponents:
    #     item = schemas.EventCreate(
    #         start_date=event.get("dtstart").dt,
    #         end_date=event.get("dtend").dt,
    #         id=event.get("uid"),
    #         guest=event.get("summary"),
    #         apartment_id=apartment_id,
    #     )
    #     events.append(item)
    #
    # try:
    #     _, created = crud.get_or_create_apartment(db, current_user.id, apartment_id, commit=False)
    #     if not created:
    #         crud.delete_apartment_events(db, apartment_id)
    #
    #     crud.create_events(db, events, commit=False)
    #     db.commit()
    # except:
    #     db.rollback()

    # TODO sta ode vratit
    return {"ok": "je"}


@app.get("/export/{apartment_id}", response_class=FileResponse)
def export_apartment_calendar(apartment_id: int, db: Session = Depends(dependencies.get_db)):

    apartment = crud.get_apartment_by_id(db, apartment_id)
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apartment not found",
        )

    c = Calendar()
    c.add("VERSION", "2.0")
    c.add("PRODID", apartment_id)
    c.add("CALSCALE", "GREGORIAN")
    c.add("METHOD", "PUBLISH")

    events = crud.get_events_by_apartment_id(db, apartment_id)
    for event in events:
        e = Event()
        e.add("DTSATRT", event.start_date)
        e.add("DTEND", event.end_date)
        e.add("UID", event.id)
        e.add("SUMMARY", event.guest)
        c.add_component(e)

    calendar = c.to_ical()
    return Response(content=calendar, media_type='text/calendar', headers={
        'content-type': 'text/calendar'
    })


@app.get("/calendars")
def get_cleaning_dates(date_from: str, date_to: str, db: Session = Depends(dependencies.get_db)):
    events = crud.get_events(db, date_from, date_to)
    print(events)
    data = utils.get_apartment_cleaning_data(events)

    return data
