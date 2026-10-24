
from parking.parking_manager import ParkingManager
from parking.database import ParkingDatabase


def get_space_number(prompt):
    """Read a valid parking-space number from 1 to 9."""
    try:
        space = int(input(prompt).strip())

        if 1 <= space <= 9:
            return space

        print("Invalid space number. Enter a number from 1 to 9.")

    except ValueError:
        print("Please enter a valid integer.")

    return None


def convert_space(space):
    """Convert space number 1-9 into row and column coordinates."""
    return (space - 1) // 3, (space - 1) % 3


def show_statistics(manager, database):
    """Display current parking status and database history totals."""
    print("\n========== PARKING STATISTICS ==========")

    print("Total capacity   :", manager.get_total_capacity())
    print("Occupied spaces  :", manager.get_occupied_spaces())
    print("Available spaces :", manager.get_available_spaces())
    print("Currently parked :", manager.get_current_vehicles())

    stats = database.get_statistics()

    print("\nCURRENT SESSION")
    print("Entries         :", manager.get_total_entries())
    print("Exits           :", manager.get_total_exits())

    print("\nDATABASE HISTORY")
    print("Recorded entries:", stats["total_entries"])
    print("Recorded exits  :", stats["total_exits"])
    print("Net recorded    :", stats["net_entries"])


def show_parking_history(database):
    """Display the most recent saved parking events."""
    history = database.get_history()

    print("\n========== PARKING HISTORY ==========")

    if not history:
        print("No parking records found.")
        return

    print(f"{'ID':<5}{'EVENT':<10}{'SPACE':<8}DATE AND TIME")
    print("-" * 65)

    for record_id, event, space, timestamp in history:
        print(f"{record_id:<5}{event:<10}{space:<8}{timestamp}")


def record_entry(manager, database, space):
    """Register a vehicle entry and record it after success."""
    row, col = convert_space(space)

    if manager.vehicle_entered(row, col):
        database.record_event("ENTRY", space)
        print(f"SUCCESS: Vehicle parked in Space {space}.")
        return True

    print("Entry rejected. No database record was added.")
    return False


def record_exit(manager, database, space):
    """Register a vehicle exit and record it after success."""
    row, col = convert_space(space)

    if manager.vehicle_exited(row, col):
        database.record_event("EXIT", space)
        print(f"SUCCESS: Vehicle exited from Space {space}.")
        return True

    print("Exit rejected. No database record was added.")
    return False


def run_demo(database):
    """Run a repeatable demonstration from an empty parking lot."""
    manager = ParkingManager(3, 3)

    print("\n========== INITIAL PARKING STATUS ==========")
    manager.display_status()

    actions = [
        ("CAR 1 ENTERS - SPACE 1", "ENTRY", 1),
        ("CAR 2 ENTERS - SPACE 5", "ENTRY", 5),
        ("CAR 3 ENTERS - SPACE 9", "ENTRY", 9),
        ("CAR 2 EXITS - SPACE 5", "EXIT", 5),
    ]

    for description, event_type, space in actions:
        print("\n" + "=" * 45)
        print(description)
        print("=" * 45)

        if event_type == "ENTRY":
            record_entry(manager, database, space)
        else:
            record_exit(manager, database, space)

        manager.display_status()

    print("\n========== DEMONSTRATION COMPLETED ==========")
    return manager


def main():
    """Run the AI Smart Parking System."""
    manager = ParkingManager(3, 3)
    database = ParkingDatabase()

    while True:
        print("\n" + "=" * 42)
        print("       AI SMART PARKING SYSTEM")
        print("=" * 42)
        print("1. Display parking status")
        print("2. Park a vehicle")
        print("3. Remove a vehicle")
        print("4. Display statistics")
        print("5. Run demonstration")
        print("6. View parking history")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            manager.display_status()

        elif choice == "2":
            space = get_space_number(
                "Enter parking space (1-9): "
            )

            if space is not None:
                record_entry(manager, database, space)
                manager.display_status()

        elif choice == "3":
            space = get_space_number(
                "Enter exiting vehicle's space (1-9): "
            )

            if space is not None:
                record_exit(manager, database, space)
                manager.display_status()

        elif choice == "4":
            show_statistics(manager, database)

        elif choice == "5":
            manager = run_demo(database)

        elif choice == "6":
            show_parking_history(database)

        elif choice == "0":
            print("Exiting AI Smart Parking System. Goodbye!")
            break

        else:
            print("Invalid choice. Select 0, 1, 2, 3, 4, 5, or 6.")


if __name__ == "__main__":
    main()
