from datetime import timedelta

import pytest

from booking_service import BookingConflict
from validation import ValidationError


def test_valid_booking_is_persisted_as_scheduled(operation, flight_window):
    database, service, aircraft_id, pilot_id = operation
    starts_at, ends_at = flight_window

    booking_id = service.book_flight(
        aircraft_id, pilot_id, "Carlos Lima", 760, starts_at, ends_at
    )

    booking = database.get_booking(booking_id)
    assert booking is not None
    assert booking["status"] == "AGENDADO"
    assert booking["aircraft_id"] == aircraft_id
    assert database.count_bookings() == 1


def test_overlapping_aircraft_booking_is_rejected_without_insert(
    operation, flight_window
):
    database, service, aircraft_id, pilot_id = operation
    starts_at, ends_at = flight_window
    service.book_flight(aircraft_id, pilot_id, "Passageiro 1", 700, starts_at, ends_at)

    with pytest.raises(BookingConflict, match="intervalo"):
        service.book_flight(
            aircraft_id,
            pilot_id,
            "Passageiro 2",
            700,
            starts_at + timedelta(minutes=30),
            ends_at + timedelta(minutes=30),
        )

    assert database.count_bookings() == 1


def test_aircraft_under_inspection_is_rejected_without_database_change(
    database, flight_window
):
    aircraft_id = database.add_aircraft("PT-MNT", 900, "EM_INSPECAO")
    pilot_id = database.add_pilot("Bruno Costa", "PLA-002")
    from booking_service import BookingService

    service = BookingService(database)
    starts_at, ends_at = flight_window

    with pytest.raises(ValidationError, match="liberada"):
        service.book_flight(
            aircraft_id, pilot_id, "Passageiro", 500, starts_at, ends_at
        )

    assert database.count_bookings() == 0


def test_each_test_starts_with_an_isolated_empty_database(operation):
    database, service, aircraft_id, pilot_id = operation

    assert database.count_bookings() == 0


def test_weight_over_capacity_is_rejected_without_insert(operation, flight_window):
    database, service, aircraft_id, pilot_id = operation
    starts_at, ends_at = flight_window

    with pytest.raises(ValidationError, match="capacidade"):
        service.book_flight(
            aircraft_id, pilot_id, "Passageiro", 901, starts_at, ends_at
        )

    assert database.count_bookings() == 0