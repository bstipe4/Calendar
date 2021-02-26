import datetime
import uuid
from typing import Optional

from pydantic import AnyUrl, BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


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
    pass


class EventBase(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    guest: str
    id: uuid.UUID
    apartment_id: int


class EventCreate(EventBase):
    pass


class Event(EventBase):
    pass


class EventInDBCustom(BaseModel):
    apartment_id: int
    gap_start: Optional[datetime.date] = None
    gap_end: Optional[datetime.date] = None
    day: datetime.date
    status: str


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        orm_mode = True


class TokenData(BaseModel):
    username: Optional[str] = None


class CalendarInputUrl(BaseModel):
    url: AnyUrl
