import cv2
import threading
import time


class CameraStream:
    """Continuously capture frames and keep only the newest frame."""

    def __init__(self, camera):
        self.camera = camera
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = True
        self.frame_ready = threading.Event()

        self.thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
        )
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            success, frame = self.camera.read()

            if success and frame is not None:
                with self.lock:
                    self.latest_frame = frame

                self.frame_ready.set()
            else:
                time.sleep(0.02)

    def read(self):
        """Return the most recently captured frame in RGB format."""
        with self.lock:
            if self.latest_frame is None:
                return None

            frame = self.latest_frame.copy()

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def close(self):
        self.running = False
        self.thread.join(timeout=2.0)
        self.camera.release()


def open_camera():
    """Open the default laptop camera."""
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        camera.release()
        raise RuntimeError(
            "Could not open laptop camera. "
            "Check Windows camera permissions and close other camera apps."
        )

    # Lower resolution reduces capture and display overhead.
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

    # Ask the driver to keep the buffer small.
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    return CameraStream(camera)


def read_camera_frame(camera_stream):
    """Get the latest available frame."""
    return camera_stream.read()


def close_camera(camera_stream):
    """Stop capture and release the camera."""
    if camera_stream is not None:
        camera_stream.close()
