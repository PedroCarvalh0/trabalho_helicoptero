from datetime import datetime, timezone
import sqlite3

from database import Database
from validation import FlightValidator


class BookingError(Exception):
    """Base exception for booking failures."""


class BookingConflict(BookingError):
    """Raised when the aircraft already has an overlapping booking."""


class BookingService:
    def __init__(self, database: Database, validator: FlightValidator | None = None):
        self.database = database
        self.validator = validator or FlightValidator()

    @staticmethod
    def _serialize_datetime(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="seconds")

    def book_flight(
        self,
        aircraft_id: int,
        pilot_id: int,
        passenger_name: str,
        total_weight_kg: float,
        starts_at: datetime,
        ends_at: datetime,
    ) -> int:
        starts = self._serialize_datetime(starts_at)
        ends = self._serialize_datetime(ends_at)
        if ends <= starts:
            raise ValueError("O horário final deve ser posterior ao inicial.")

        with self.database.transaction() as connection:
            aircraft = connection.execute(
                "SELECT * FROM aircraft WHERE id = ?", (aircraft_id,)
            ).fetchone()
            if aircraft is None:
                raise ValueError("Aeronave não encontrada.")

            self.validator.validate(aircraft, total_weight_kg)
            if self.database.has_booking_conflict(connection, aircraft_id, starts, ends):
                raise BookingConflict("A aeronave já possui voo nesse intervalo.")

            try:
                cursor = connection.execute(
                    """INSERT INTO bookings
                       (aircraft_id, pilot_id, passenger_name, total_weight_kg,
                        starts_at, ends_at, status)
                       VALUES (?, ?, ?, ?, ?, ?, 'AGENDADO')""",
                    (
                        aircraft_id,
                        pilot_id,
                        passenger_name,
                        total_weight_kg,
                        starts,
                        ends,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise BookingError(f"Não foi possível registrar o agendamento: {error}") from error
            return int(cursor.lastrowid)