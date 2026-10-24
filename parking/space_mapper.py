"""
space_mapper.py
====================================================
Maps YOLO vehicle detections to a 3x3 parking grid.

Row-wise numbering:
    1 | 2 | 3
    4 | 5 | 6
    7 | 8 | 9

Grid boundaries are calibrated approximately from
the supplied parking image (706 x 525 pixels).
For other images or camera views, recalibration may
be required.
====================================================
"""

# Normalized vertical boundaries between columns.
X_BOUNDS = [0.0, 0.3314, 0.6629, 1.0]

# Normalized horizontal boundaries between rows.
Y_BOUNDS = [0.0, 0.3295, 0.6648, 1.0]

SUPPORTED_VEHICLES = {
    "Car",
    "Motorcycle",
    "Bus",
    "Truck",
}


def _validate_bounds(bounds, name):
    """Validate four increasing normalized grid boundaries."""

    if len(bounds) != 4:
        raise ValueError(
            f"{name} must contain exactly four values."
        )

    if any(
        not isinstance(value, (int, float))
        for value in bounds
    ):
        raise ValueError(
            f"{name} values must be numeric."
        )

    if bounds[0] != 0.0 or bounds[-1] != 1.0:
        raise ValueError(
            f"{name} must start at 0.0 and end at 1.0."
        )

    if any(
        bounds[i] >= bounds[i + 1]
        for i in range(3)
    ):
        raise ValueError(
            f"{name} values must be strictly increasing."
        )


def _find_region(value, bounds):
    """
    Return a zero-based row or column index.

    Internal boundaries belong to the region to their
    right or below. Coordinate 1.0 belongs to the
    final region.
    """

    if value < bounds[0] or value > bounds[-1]:
        return None

    for index in range(3):
        if bounds[index] <= value < bounds[index + 1]:
            return index

    if value == bounds[-1]:
        return 2

    return None


def map_vehicles_to_spaces(
    detections,
    image_width,
    image_height,
):
    """
    Map detected vehicles to row-wise parking spaces.

    Parameters
    ----------
    detections : list
        Each supported detection must contain:
        vehicle, x1, y1, x2, y2.

    image_width : int or float
        Original image width in pixels.

    image_height : int or float
        Original image height in pixels.

    Returns
    -------
    mapped : list
        Supported detections with an added space_number.

    occupied_spaces : list
        Sorted list of unique occupied space numbers.
    """

    # Validate image dimensions.
    if (
        not isinstance(image_width, (int, float))
        or not isinstance(image_height, (int, float))
        or image_width <= 0
        or image_height <= 0
    ):
        raise ValueError(
            "Image width and height must be positive numbers."
        )

    _validate_bounds(X_BOUNDS, "X_BOUNDS")
    _validate_bounds(Y_BOUNDS, "Y_BOUNDS")

    mapped = []
    occupied_spaces = set()

    # Process every vehicle detection.
    for index, detection in enumerate(detections):

        if not isinstance(detection, dict):
            raise TypeError(
                f"Detection {index} must be a dictionary."
            )

        # Ignore unsupported object classes.
        if detection.get("vehicle") not in SUPPORTED_VEHICLES:
            continue

        # Read and validate bounding-box coordinates.
        try:
            x1, y1, x2, y2 = (
                float(detection[key])
                for key in ("x1", "y1", "x2", "y2")
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Detection {index} must contain numeric "
                "x1, y1, x2, y2 coordinates."
            ) from exc

        if x2 < x1 or y2 < y1:
            raise ValueError(
                f"Detection {index} has reversed coordinates."
            )

        # Ignore zero-area bounding boxes.
        if x2 == x1 or y2 == y1:
            continue

        # Find the bounding-box centre.
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0

        # Normalize coordinates to the range 0.0-1.0.
        normalized_x = center_x / image_width
        normalized_y = center_y / image_height

        # Find column and row.
        col = _find_region(normalized_x, X_BOUNDS)
        row = _find_region(normalized_y, Y_BOUNDS)

        # Ignore centres outside the image.
        if row is None or col is None:
            continue

        # Row-wise numbering:
        # Top row:    1, 2, 3
        # Middle row: 4, 5, 6
        # Bottom row: 7, 8, 9
        space_number = row * 3 + col + 1

        occupied_spaces.add(space_number)

        # Preserve original detection data.
        mapped.append({
            **detection,
            "space_number": space_number,
        })

    return mapped, sorted(occupied_spaces)


# ----------------------------------------------------
# STANDALONE TEST
# ----------------------------------------------------

if __name__ == "__main__":

    sample_detections = [
        {
            "vehicle": "Car",
            "confidence": 0.90,
            "x1": 60,
            "y1": 20,
            "x2": 180,
            "y2": 150,
        },
        {
            "vehicle": "Motorcycle",
            "confidence": 0.80,
            "x1": 70,
            "y1": 360,
            "x2": 150,
            "y2": 460,
        },
    ]

    mapped, occupied = map_vehicles_to_spaces(
        sample_detections,
        image_width=705,
        image_height=500,
    )

    print("\nAI SMART PARKING - SPACE MAPPER")
    print("-" * 35)

    print("\nMapped vehicles:")

    for item in mapped:
        print(
            f'{item["vehicle"]} -> '
            f'Space {item["space_number"]}'
        )

    print("\nOccupied spaces:", occupied)
    print(
        "Available spaces:",
        sorted(set(range(1, 10)) - set(occupied)),
    )

    print("-" * 35)
