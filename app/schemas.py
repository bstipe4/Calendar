import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, Field, AnyUrl


class UserBase(BaseModel):
    username: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        orm_mode = True


class ApartmentBase(BaseModel):
    id: str
    owner_id: int
    calendar_url: Optional[AnyUrl] = None


class ApartmentCreate(ApartmentBase):
    pass


class Apartment(ApartmentBase):
    owner: User

    class Config:
        orm_mode = True


class EventBase(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    guest: str
    id: uuid.UUID
    apartment_id: int


class EventCreate(EventBase):
    url: Optional[str] = None


class Event(EventBase):
    pass


class EventInDBCustom(BaseModel):
    apartment_id: int
    gap_start: Optional[datetime.date] = None
    gap_end: Optional[datetime.date] = None
    day: datetime.date
    status: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class CalendarInputUrl(BaseModel):
    url: AnyUrl
