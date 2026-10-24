
from pathlib import Path

import numpy as np
from PIL import Image
from ultralytics import YOLO


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MODEL_NAME = "yolo11s.pt"

VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
}


# --------------------------------------------------
# LOAD YOLO MODEL
# --------------------------------------------------

model = YOLO(MODEL_NAME)


# --------------------------------------------------
# VEHICLE DETECTION FUNCTION
# --------------------------------------------------

def detect_vehicles(image_path, confidence=0.35):
    """
    Detect cars, motorcycles, buses, and trucks.

    Parameters
    ----------
    image_path:
        Image file path, PIL Image, or NumPy image array.

    confidence:
        Minimum detection confidence between 0.0 and 1.0.

    Returns
    -------
    annotated_image:
        YOLO-annotated image in BGR format.

    detections:
        List of supported vehicle detections and coordinates.

    vehicle_count:
        Number of supported vehicles detected.
    """

    # Validate confidence.
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not np.isfinite(confidence)
        or not 0.0 <= confidence <= 1.0
    ):
        raise ValueError(
            "Confidence must be a finite number between 0.0 and 1.0."
        )

    # Accept file paths, PIL images, or NumPy arrays.
    if isinstance(image_path, (str, Path)):
        image_source = Path(image_path)

        if not image_source.is_file():
            raise FileNotFoundError(
                f"Image file not found: {image_source}"
            )

        image_source = str(image_source)

    elif isinstance(image_path, Image.Image):
        image_source = np.array(image_path.convert("RGB"))

    elif isinstance(image_path, np.ndarray):
        if image_path.size == 0:
            raise ValueError("Input image array cannot be empty.")

        if image_path.ndim not in (2, 3):
            raise ValueError(
                "Image array must have 2 or 3 dimensions."
            )

        image_source = image_path

    else:
        raise TypeError(
            "Input must be a file path, PIL Image, "
            "or NumPy array."
        )

    # Run YOLO inference using the selected confidence value.
    results = model.predict(
        source=image_source,
        conf=float(confidence),
        iou=0.45,
        agnostic_nms=True,
        verbose=False,
    )

    if not results:
        raise RuntimeError("YOLO did not return an inference result.")

    result = results[0]
    detections = []

    # Process detected bounding boxes.
    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0].item())

            # Keep only supported vehicle classes.
            if class_id not in VEHICLE_CLASSES:
                continue

            score = float(box.conf[0].item())

            x1, y1, x2, y2 = (
                int(value)
                for value in box.xyxy[0].tolist()
            )

            detections.append({
                "vehicle": VEHICLE_CLASSES[class_id],
                "confidence": round(score, 3),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            })

    # YOLO plot() returns an annotated BGR image.
    annotated_image = result.plot()
    vehicle_count = len(detections)

    return annotated_image, detections, vehicle_count


# --------------------------------------------------
# STANDALONE TEST
# --------------------------------------------------

if __name__ == "__main__":
    print("AI Smart Parking - Vehicle Detection")
    print("YOLO model:", MODEL_NAME)
    print(
        "Supported classes:",
        ", ".join(VEHICLE_CLASSES.values()),
    )

    test_image = input(
        "\nEnter an image path to test, or press Enter to exit: "
    ).strip().strip('"')

    if test_image:
        try:
            annotated, detections, count = detect_vehicles(
                test_image,
                confidence=0.35,
            )

            print(f"\nDetected vehicles: {count}")

            for index, detection in enumerate(detections, start=1):
                print(
                    f"{index}. {detection['vehicle']} | "
                    f"Confidence: {detection['confidence']:.1%} | "
                    f"Box: ({detection['x1']}, {detection['y1']}, "
                    f"{detection['x2']}, {detection['y2']})"
                )

            output_path = Path(test_image).with_name(
                Path(test_image).stem + "_detected.jpg"
            )

            # Convert BGR to RGB before saving with Pillow.
            annotated_rgb = annotated[:, :, ::-1]
            Image.fromarray(annotated_rgb).save(output_path)

            print(f"\nAnnotated image saved to: {output_path}")

        except Exception as error:
            print(f"\nDetection failed: {error}")
