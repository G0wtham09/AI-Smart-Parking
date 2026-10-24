import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import closing


# Store the database in the main AI_Smart_Parking folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "parking.db"


class ParkingDatabase:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.create_table()

    def connect(self):
        """Create a new SQLite connection."""
        return sqlite3.connect(self.db_path)

    def create_table(self):
        """Create required tables and initialize nine parking spaces."""
        with closing(self.connect()) as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS parking_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        space_number INTEGER NOT NULL,
                        event_time TEXT NOT NULL
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS parking_spaces (
                        space_number INTEGER PRIMARY KEY,
                        occupied INTEGER NOT NULL DEFAULT 0
                    )
                """)

                conn.executemany("""
                    INSERT OR IGNORE INTO parking_spaces
                    (space_number, occupied)
                    VALUES (?, 0)
                """, [(space,) for space in range(1, 10)])

    def record_event(self, event_type, space_number):
        """
        Record an entry or exit and update occupancy atomically.
        If either operation fails, both changes are rolled back.
        """
        if event_type not in ("ENTRY", "EXIT"):
            raise ValueError("Event type must be ENTRY or EXIT.")

        if (
            not isinstance(space_number, int)
            or isinstance(space_number, bool)
            or not 1 <= space_number <= 9
        ):
            raise ValueError(
                "Space number must be an integer between 1 and 9."
            )

        timestamp = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
        occupied = 1 if event_type == "ENTRY" else 0

        with closing(self.connect()) as conn:
            with conn:
                conn.execute("""
                    INSERT INTO parking_history
                    (event_type, space_number, event_time)
                    VALUES (?, ?, ?)
                """, (event_type, space_number, timestamp))

                conn.execute("""
                    INSERT INTO parking_spaces (space_number, occupied)
                    VALUES (?, ?)
                    ON CONFLICT(space_number)
                    DO UPDATE SET occupied = excluded.occupied
                """, (space_number, occupied))

    def get_occupied_spaces(self):
        """Return occupied space numbers in ascending order."""
        with closing(self.connect()) as conn:
            rows = conn.execute("""
                SELECT space_number
                FROM parking_spaces
                WHERE occupied = 1
                ORDER BY space_number
            """).fetchall()

        return [row[0] for row in rows]

    def get_history(self, limit=50):
        """Return newest history rows first."""
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
        ):
            raise ValueError("limit must be a positive integer.")

        with closing(self.connect()) as conn:
            rows = conn.execute("""
                SELECT id, event_type, space_number, event_time
                FROM parking_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()

        return rows

    def get_history_between(
        self, start_iso, end_iso, limit=100000
    ):
        """
        Return events in [start_iso, end_iso), newest first.

        Timestamps are stored as ISO-8601 text. Pass consistently
        formatted timestamps when using this method directly.
        """
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < 1
        ):
            raise ValueError("limit must be a positive integer.")

        with closing(self.connect()) as conn:
            rows = conn.execute("""
                SELECT id, event_type, space_number, event_time
                FROM parking_history
                WHERE event_time >= ? AND event_time < ?
                ORDER BY event_time DESC, id DESC
                LIMIT ?
            """, (start_iso, end_iso, limit)).fetchall()

        return rows

    def get_statistics(self):
        """Return total entry, exit, and net event counts."""
        with closing(self.connect()) as conn:
            entries, exits = conn.execute("""
                SELECT
                    SUM(
                        CASE WHEN event_type = 'ENTRY'
                        THEN 1 ELSE 0 END
                    ),
                    SUM(
                        CASE WHEN event_type = 'EXIT'
                        THEN 1 ELSE 0 END
                    )
                FROM parking_history
            """).fetchone()

        entries = entries or 0
        exits = exits or 0

        return {
            "total_entries": entries,
            "total_exits": exits,
            "net_entries": entries - exits,
        }
