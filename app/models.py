from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True)
    hashed_password = Column(String, nullable=False)


class Apartment(Base):
    __tablename__ = "apartments"
    # TODO stavi cascade ode di triba
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    calendar_url = Column(String, nullable=True)
    owner = relationship("User", cascade="all, delete")


# class Calendar(Base):
#     __tablename__ = "calendars"
#
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     url = Column(String, nullable=True)
#
#     user = relationship("User")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    start_date = Column(Date)
    end_date = Column(Date)
    guest = Column(String, nullable=False)
    apartment_id = Column(Integer, ForeignKey("apartments.id"))
    # calendar_id = Column(Integer, ForeignKey("calendars.id"))

    # guest = relationship("Guest")
    apartment = relationship("Apartment", cascade="all, delete")
    # calendar = relationship("Calendar")


# class Guest(Base):
#     __tablename__ = "guests"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
