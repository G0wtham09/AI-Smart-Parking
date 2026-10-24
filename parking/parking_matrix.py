class ParkingMatrix:

    def __init__(self, rows=3, columns=3):
        self.rows = rows
        self.columns = columns

        # 0 = vacant
        # 1 = occupied
        self.matrix = [
            [0 for _ in range(columns)]
            for _ in range(rows)
        ]

    def occupy_space(self, row, column):
        """Mark a parking space as occupied."""

        if not self._valid_position(row, column):
            return False

        self.matrix[row][column] = 1
        return True

    def release_space(self, row, column):
        """Mark a parking space as vacant."""

        if not self._valid_position(row, column):
            return False

        self.matrix[row][column] = 0
        return True

    def is_occupied(self, row, column):
        """Check whether a parking space is occupied."""

        if not self._valid_position(row, column):
            return False

        return self.matrix[row][column] == 1

    def get_occupied_count(self):
        """Return the number of occupied spaces."""

        return sum(sum(row) for row in self.matrix)

    def get_available_count(self):
        """Return the number of available spaces."""

        total_spaces = self.rows * self.columns
        occupied_spaces = self.get_occupied_count()

        return total_spaces - occupied_spaces

    def get_total_spaces(self):
        """Return total parking capacity."""

        return self.rows * self.columns

    def is_full(self):
        """Check whether all parking spaces are occupied."""

        return self.get_available_count() == 0

    def is_empty(self):
        """Check whether all parking spaces are vacant."""

        return self.get_occupied_count() == 0

    def get_matrix(self):
        """Return the current parking matrix."""

        return self.matrix

    def _valid_position(self, row, column):
        """Check whether a matrix position is valid."""

        return (
            0 <= row < self.rows
            and
            0 <= column < self.columns
        )