class VehicleCounter:
    """
    Tracks vehicle entry and exit statistics.
    """

    def __init__(self):
        self.entries = 0
        self.exits = 0

    # -------------------------------------------------
    # VEHICLE ENTRY
    # -------------------------------------------------

    def vehicle_entered(self):
        """Increase the vehicle entry count."""
        self.entries += 1

    # -------------------------------------------------
    # VEHICLE EXIT
    # -------------------------------------------------

    def vehicle_exited(self):
        """Increase the vehicle exit count."""
        self.exits += 1

    # -------------------------------------------------
    # STATISTICS
    # -------------------------------------------------

    def get_entries(self):
        """Return total vehicles entered."""
        return self.entries

    def get_exits(self):
        """Return total vehicles exited."""
        return self.exits

    def get_current_vehicles(self):
        """Return the number of vehicles currently inside."""
        return self.entries - self.exits

    def reset(self):
        """Reset all counter values."""
        self.entries = 0
        self.exits = 0

    # -------------------------------------------------
    # DISPLAY
    # -------------------------------------------------

    def display(self):
        """Display current vehicle statistics."""

        print("\n" + "=" * 40)
        print("       VEHICLE COUNTER")
        print("=" * 40)

        print("Total Vehicles Entered :", self.entries)
        print("Total Vehicles Exited  :", self.exits)
        print("Currently Inside       :", self.get_current_vehicles())

        print("=" * 40)