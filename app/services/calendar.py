from collections import defaultdict
from typing import List

from icalendar import Calendar, Event

from app import crud, requests, schemas


def get_calendar_with_proposed_cleaning_days(db, user_id, date_from, date_to):
    events = crud.get_events_with_statuses_per_day(db, user_id, date_from, date_to)
    calendar = _get_apartment_cleaning_data(events)
    return calendar


def generate_apartment_calendar(db, apartment_id):

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

    calendar_data = c.to_ical()
    return calendar_data


def import_calendar_from_file(db, user_id, file):
    c = Calendar.from_ical(file)
    apartment_id = c.get("prodid")

    events = _get_events_from_calendar(c)

    events = [
        schemas.EventCreate(**event, apartment_id=apartment_id) for event in events
    ]

    crud.insert_or_update_apartment_calendar(db, user_id, apartment_id, events)


def import_calendar_from_url(db, user_id, url):
    file = requests.get_file_from_url(url)
    c = Calendar.from_ical(file)

    apartment_id = c.get("prodid")
    events = _get_events_from_calendar(c)
    events = [
        schemas.EventCreate(**event, apartment_id=apartment_id) for event in events
    ]

    crud.insert_or_update_apartment_calendar(db, user_id, apartment_id, events)


def _get_events_from_calendar(calendar):
    events = []
    for event in calendar.subcomponents:
        events.append(
            {
                "start_date": event.get("dtstart").dt,
                "end_date": event.get("dtend").dt,
                "id": event.get("uid"),
                "guest": event.get("summary"),
            }
        )

    return events


def _get_apartment_cleaning_data(events: List[schemas.EventInDBCustom]):

    guest_shift_dates = set()

    calendar_data = defaultdict(
        lambda: {
            "possible_clean_days": set(),
            "periods": set(),
            "dates": defaultdict(lambda: set()),
        }
    )

    for event in events:
        if event.gap_start and event.gap_end:
            # these events represent days when apartments can be cleaned
            guest_shift_dates.add(event.gap_start)
            guest_shift_dates.add(event.gap_end)

            calendar_data[event.apartment_id]["possible_clean_days"].add(event.day)
            apartment_free_period = (event.gap_start, event.gap_end)
            calendar_data[event.apartment_id]["periods"].add(apartment_free_period)

        calendar_data[event.apartment_id]["dates"][event.day].add(event.status)

    # check which guest shift date has the most possible cleanings
    cleanings_per_shift_day = defaultdict(lambda: set())
    for day in guest_shift_dates:
        for apartment in list(calendar_data):
            if day in calendar_data[apartment]["possible_clean_days"]:
                cleanings_per_shift_day[day].add(apartment)

    for day in sorted(
        cleanings_per_shift_day,
        key=lambda k: len(cleanings_per_shift_day[k]),
        reverse=True,
    ):

        # begin with the date that suits for the most apartments
        for apartment in cleanings_per_shift_day[day]:
            if len(calendar_data[apartment]["periods"]) == 0:
                # apartment has filled cleaning schedule between guest shifts
                continue

            item_to_delete = None
            for date_range in calendar_data[apartment]["periods"]:
                if date_range[0] <= day <= date_range[1]:
                    # apartment not cleaned for that period, clean it!
                    calendar_data[apartment]["dates"][day].add("SPREMANJE")
                    item_to_delete = (
                        date_range  # we scheduled cleaning for that period, remove it
                    )

            if item_to_delete:
                calendar_data[apartment]["periods"].remove(item_to_delete)

    return calendar_data
