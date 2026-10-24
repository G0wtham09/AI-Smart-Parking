
from parking.parking_matrix import ParkingMatrix


class ParkingManager:
    """
    Manages vehicle entry, exit, parking occupancy,
    and available-space information.
    """

    def __init__(self, rows=3, columns=3):
        if (
            not isinstance(rows, int)
            or isinstance(rows, bool)
            or rows <= 0
        ):
            raise ValueError("Rows must be a positive integer.")

        if (
            not isinstance(columns, int)
            or isinstance(columns, bool)
            or columns <= 0
        ):
            raise ValueError("Columns must be a positive integer.")

        self.rows = rows
        self.columns = columns
        self.parking = ParkingMatrix(rows, columns)

        self.total_entries = 0
        self.total_exits = 0

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    def _validate_position(self, row, column):
        """Validate a zero-based parking matrix position."""
        if (
            not isinstance(row, int)
            or isinstance(row, bool)
            or not isinstance(column, int)
            or isinstance(column, bool)
        ):
            raise ValueError(
                "Row and column must be integers."
            )

        if not (0 <= row < self.rows):
            raise ValueError(
                f"Row must be between 0 and {self.rows - 1}."
            )

        if not (0 <= column < self.columns):
            raise ValueError(
                f"Column must be between 0 and {self.columns - 1}."
            )

    # -------------------------------------------------
    # VEHICLE ENTRY
    # -------------------------------------------------

    def vehicle_entered(self, row, column):
        """
        Register a vehicle entering the parking lot.

        Returns True when successful and False when the
        lot is full or the selected space is occupied.

        Raises ValueError for invalid coordinates.
        """
        self._validate_position(row, column)

        if self.parking.is_full():
            print("Parking is FULL. Entry rejected.")
            return False

        if self.parking.is_occupied(row, column):
            print("Selected parking space is already occupied.")
            return False

        self.parking.occupy_space(row, column)
        self.total_entries += 1

        return True

    # -------------------------------------------------
    # VEHICLE EXIT
    # -------------------------------------------------

    def vehicle_exited(self, row, column):
        """
        Register a vehicle leaving the parking lot.

        Returns True when successful and False when the
        selected space is already vacant.

        Raises ValueError for invalid coordinates.
        """
        self._validate_position(row, column)

        if not self.parking.is_occupied(row, column):
            print("Selected parking space is already vacant.")
            return False

        self.parking.release_space(row, column)
        self.total_exits += 1

        return True

    # -------------------------------------------------
    # PARKING INFORMATION
    # -------------------------------------------------

    def get_total_capacity(self):
        """Return total parking capacity."""
        return self.parking.get_total_spaces()

    def get_occupied_spaces(self):
        """Return the number of occupied spaces."""
        return self.parking.get_occupied_count()

    def get_available_spaces(self):
        """Return the number of available spaces."""
        return self.parking.get_available_count()

    def get_total_entries(self):
        """Return the total number of successful entries."""
        return self.total_entries

    def get_total_exits(self):
        """Return the total number of successful exits."""
        return self.total_exits

    def get_current_vehicles(self):
        """Return the net number of vehicles currently inside."""
        return self.total_entries - self.total_exits

    def get_matrix(self):
        """Return the current parking matrix."""
        return self.parking.get_matrix()

    def is_full(self):
        """Return True if all parking spaces are occupied."""
        return self.parking.is_full()

    def is_empty(self):
        """Return True if all parking spaces are vacant."""
        return self.parking.is_empty()

    # -------------------------------------------------
    # DISPLAY STATUS
    # -------------------------------------------------

    def display_status(self):
        """Print the current parking status."""
        print("\n" + "=" * 45)
        print("       AI SMART PARKING STATUS")
        print("=" * 45)

        print("\nParking Matrix:")
        for row in self.get_matrix():
            print(row)

        print("\nTotal Capacity :", self.get_total_capacity())
        print("Occupied       :", self.get_occupied_spaces())
        print("Available      :", self.get_available_spaces())

        print("\nTotal Entries  :", self.get_total_entries())
        print("Total Exits    :", self.get_total_exits())
        print("Currently Parked:", self.get_current_vehicles())

        print("\nParking Full   :", self.is_full())
        print("Parking Empty  :", self.is_empty())

        print("=" * 45)
