"""
produce.py  –  stream/produce.py

CameraProducer captures frames, runs optional motion detection, adds overlay,
then:

  1. Calls MotionSnapshot.on_frame() to save a JPEG still on motion events.
  2. Calls CameraRecorder.write() to append to the rolling MP4 clip.
  3. Pushes the encoded JPEG into a FrameBuffer for all streaming clients.
"""

from utils.motion import MotionDetector
from utils.overlays import add_overlay
from utils.frame_buffer import get_or_create as get_frame_buffer
from utils.recorder import CameraRecorder, MotionSnapshot
import cv2
import time
import threading


class CameraProducer:
    def __init__(self, cam_index, pipe_dir=None,
                 width=320, height=240, fps=10, motion_area=500, config=None):
        self.cam_index = cam_index
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config
        self.frame_interval = 1.0 / fps

        # Shared frame buffer – one per camera, many clients can read it
        self.frame_buffer = get_frame_buffer(cam_index)

        # Recording & snapshots
        self.recorder = CameraRecorder(cam_index, config)
        self.snapshotter = MotionSnapshot(cam_index, config)

        # Motion detector (only created if enabled)
        self.motion_detector = MotionDetector(contour_area=motion_area) if config.motion_detection else None

        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True,
                                       name=f"producer-cam{cam_index}")

        # Cache motion state to avoid running detection on every frame
        self.motion_check_interval = 3
        self.last_motion_state = False

    def start(self):
        self._stop_event.clear()
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.thread.join(timeout=5.0)
        self.recorder.stop()
        self.frame_buffer.close()

    def _run(self):
        cap = cv2.VideoCapture(self.cam_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.cam_index)

        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        encode_params = [
            int(cv2.IMWRITE_JPEG_QUALITY), 60,
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
            int(cv2.IMWRITE_JPEG_PROGRESSIVE), 0,
        ]

        frame_count = 0
        next_frame_time = time.monotonic()

        try:
            while not self._stop_event.is_set():
                now = time.monotonic()
                sleep_for = next_frame_time - now
                if sleep_for > 0.001:
                    time.sleep(sleep_for)
                next_frame_time = time.monotonic() + self.frame_interval

                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.02)
                    continue

                # ---- Motion detection (sampled every Nth frame) ----------
                motion_detected = self.last_motion_state
                if self.motion_detector and frame_count % self.motion_check_interval == 0:
                    motion_detected, frame = self.motion_detector.detect(frame)
                    self.last_motion_state = motion_detected

                # ---- Overlay for live view ------------------------------
                display_frame = add_overlay(frame, self.cam_index, motion_detected)
                
                # ---- Rolling MP4 recording (raw frame, no overlay) -------
                self.recorder.write(display_frame)
                
                # ---- Snapshot on motion event (raw frame, no overlay) ----
                self.snapshotter.on_frame(display_frame, motion_detected)

                # ---- Encode and push to frame buffer --------------------
                ret_enc, jpeg = cv2.imencode('.jpg', display_frame, encode_params)
                if ret_enc:
                    self.frame_buffer.push(jpeg.tobytes())

                frame_count += 1

        finally:
            cap.release()