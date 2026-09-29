from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _read_connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._read_connection() as connection:
            with connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS aircraft (
                        id INTEGER PRIMARY KEY,
                        registration TEXT NOT NULL UNIQUE,
                        useful_load_kg REAL NOT NULL CHECK (useful_load_kg > 0),
                        maintenance_status TEXT NOT NULL
                            CHECK (maintenance_status IN ('LIBERADO', 'EM_INSPECAO'))
                    );
                    CREATE TABLE IF NOT EXISTS pilots (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        license_number TEXT NOT NULL UNIQUE
                    );
                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY,
                        aircraft_id INTEGER NOT NULL REFERENCES aircraft(id),
                        pilot_id INTEGER NOT NULL REFERENCES pilots(id),
                        passenger_name TEXT NOT NULL,
                        total_weight_kg REAL NOT NULL CHECK (total_weight_kg > 0),
                        starts_at TEXT NOT NULL,
                        ends_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'AGENDADO'
                            CHECK (status IN ('AGENDADO')),
                        CHECK (ends_at > starts_at)
                    );
                    CREATE INDEX IF NOT EXISTS idx_bookings_aircraft_interval
                        ON bookings(aircraft_id, starts_at, ends_at);
                    """
                )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_aircraft(
        self, registration: str, useful_load_kg: float, maintenance_status: str
    ) -> int:
        with self.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO aircraft (registration, useful_load_kg, maintenance_status) "
                "VALUES (?, ?, ?)",
                (registration, useful_load_kg, maintenance_status),
            )
            return int(cursor.lastrowid)

    def add_pilot(self, name: str, license_number: str) -> int:
        with self.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO pilots (name, license_number) VALUES (?, ?)",
                (name, license_number),
            )
            return int(cursor.lastrowid)

    def get_aircraft(self, aircraft_id: int) -> sqlite3.Row | None:
        with self._read_connection() as connection:
            return connection.execute(
                "SELECT * FROM aircraft WHERE id = ?", (aircraft_id,)
            ).fetchone()

    def has_booking_conflict(
        self,
        connection: sqlite3.Connection,
        aircraft_id: int,
        starts_at: str,
        ends_at: str,
    ) -> bool:
        return connection.execute(
            """SELECT 1 FROM bookings
               WHERE aircraft_id = ? AND starts_at < ? AND ends_at > ? LIMIT 1""",
            (aircraft_id, ends_at, starts_at),
        ).fetchone() is not None

    def get_booking(self, booking_id: int) -> sqlite3.Row | None:
        with self._read_connection() as connection:
            return connection.execute(
                "SELECT * FROM bookings WHERE id = ?", (booking_id,)
            ).fetchone()

    def count_bookings(self) -> int:
        with self._read_connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0])