from collections import defaultdict
from typing import List
from . import schemas


def get_apartment_cleaning_data(events: List[schemas.EventInDBCustom]):

    guest_shift_dates = set()

    calendar_data = defaultdict(lambda: {
        "possible_clean_days": set(),
        "periods": set(),
        "dates": defaultdict(lambda: set())
    })

    for event in events:
        if event.gap_start and event.gap_end:
            guest_shift_dates.add(event.gap_start)
            guest_shift_dates.add(event.gap_end)

            calendar_data[event.apartment_id]['possible_clean_days'].add(event.day)
            apartment_free_period = (event.gap_start, event.gap_end)
            calendar_data[event.apartment_id]['periods'].add(apartment_free_period)

        calendar_data[event.apartment_id]["dates"][event.day].add(event.status)

    # check which guest shift date has the most possible cleanings
    cleanings_per_shift_day = defaultdict(lambda: set())
    for day in guest_shift_dates:
        for apartment in list(calendar_data):
            if day in calendar_data[apartment]['possible_clean_days']:
                cleanings_per_shift_day[day].add(apartment)

    for day in sorted(cleanings_per_shift_day, key=lambda k: len(cleanings_per_shift_day[k]), reverse=True):

        # begin with the date that suits for the most apartments
        for apartment in cleanings_per_shift_day[day]:
            if len(calendar_data[apartment]['periods']) == 0:
                # apartment has filled cleaning schedule between guest shifts
                continue

            item_to_delete = None
            for date_range in calendar_data[apartment]['periods']:
                if date_range[0] <= day <= date_range[1]:
                    # apartment not cleaned for that period, clean it!
                    calendar_data[apartment]['dates'][day].add("SPREMANJE")
                    item_to_delete = date_range
                    # we scheduled cleaning for that period, remove it
            if item_to_delete:
                calendar_data[apartment]['periods'].remove(item_to_delete)

    return calendar_data
