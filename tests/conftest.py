from datetime import datetime, timezone

import pytest

from database import Database
from booking_service import BookingService


@pytest.fixture
def database(tmp_path):
    return Database(tmp_path / "flight_test.sqlite3")


@pytest.fixture
def operation(database):
    aircraft_id = database.add_aircraft("PT-HLX", 900, "LIBERADO")
    pilot_id = database.add_pilot("Ana Silva", "PLA-001")
    return database, BookingService(database), aircraft_id, pilot_id


@pytest.fixture
def flight_window():
    return (
        datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc),
    )