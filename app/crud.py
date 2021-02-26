from typing import List

from sqlalchemy.orm import Session

from app import auth, models, schemas


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_apartment_by_id(db: Session, user_id, apartment_id):
    return (
        db.query(models.Apartment)
        .filter(
            models.Apartment.id == apartment_id, models.Apartment.owner_id == user_id
        )
        .first()
    )


def create_apartment(db: Session, apartment: schemas.ApartmentCreate, commit=True):
    db_item = models.Apartment(**apartment.dict())
    db.add(db_item)
    db.flush([db_item])
    if commit:
        db.commit()
    return db_item


def get_or_create_apartment(
    db: Session, owner_id: int, apartment_id: str, calendar_url=None, commit=True
):
    db_item = get_apartment_by_id(db, owner_id, apartment_id)
    if db_item:
        return db_item, False

    db_item = create_apartment(
        db,
        schemas.ApartmentCreate(
            id=apartment_id, owner_id=owner_id, calendar_url=calendar_url
        ),
        commit,
    )
    return db_item, True


def create_events(db: Session, events: List[schemas.EventCreate], commit=True):
    db_items = [models.Event(**event.dict()) for event in events]
    db.bulk_save_objects(db_items)
    if commit:
        db.commit()


def delete_apartment_events(db: Session, apartment_id: str):
    db.query(models.Event).filter_by(apartment_id=apartment_id).delete()
    db.commit()


def get_events_by_apartment_id(db: Session, apartment_id):
    return db.query(models.Event).filter_by(apartment_id=apartment_id).all()


def insert_or_update_apartment_calendar(
    db, user_id, apartment_id, events: List[schemas.EventCreate]
):
    # begin transaction
    _, created = get_or_create_apartment(db, user_id, apartment_id, commit=False)
    if not created:
        delete_apartment_events(db, apartment_id)

    create_events(db, events, commit=False)

    # end transaction
    db.commit()


def get_events_with_statuses_per_day(db: Session, owner_id, date_from, date_to):
    db_items = db.execute(
        f"""SELECT
      *
    FROM ( (
    WITH
      gap_data AS (
      SELECT
        apartment_id,
        start_date,
        end_date,
        prev_end_time AS gap_start_time,
        start_date AS gap_end_time,
        generate_series(prev_end_time::date,
          start_date::date,
          '1 day')::date apartment_date
      FROM (
        SELECT
          *,
          LAG(end_date) OVER (PARTITION BY apartment_id ORDER BY start_date) AS prev_end_time
        FROM
          events
        ORDER BY
          start_date ) a
      WHERE
        start_date >= prev_end_time)
    SELECT
      apartment_id,
      gap_start_time AS start_date,
      gap_end_time AS end_date,
      apartment_date,
      CASE
        WHEN gap_start_time = apartment_date THEN 'izlazak'
        WHEN gap_end_time = apartment_date THEN 'ulazak'
      ELSE
      'slobodno'
    END
      AS status
    FROM
      gap_data gd )
  UNION ALL (
    SELECT
      apartment_id,
      NULL AS start_date,
      NULL AS end_date,
      booked_day,
      CASE
        WHEN booked_day = start_date::date THEN 'ulazak'
        WHEN booked_day = end_date::date THEN 'izlazak'
      ELSE
      'zauzeto'
    END
      AS status
    FROM (
      SELECT
        apartment_id,
        start_date,
        end_date,
        generate_series(start_date::date,
          end_date::date,
          '1 day')::date booked_day
      FROM
        events ) ev ) ) status_per_day
      INNER JOIN apartments aps on apartment_id = aps.id
      WHERE aps.owner_id = {owner_id}
	  AND apartment_date BETWEEN '{date_from}' AND '{date_to}'
	  ORDER BY apartment_date
"""
    )

    output = [
        schemas.EventInDBCustom(
            apartment_id=item[0],
            gap_start=item[1],
            gap_end=item[2],
            day=item[3],
            status=item[4],
        )
        for item in db_items
    ]

    return output
