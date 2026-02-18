"""
recorder.py  –  utils/recorder.py

Two classes:

  CameraRecorder    – writes rolling MP4 clips, cleans up old ones.
  MotionSnapshot    – saves a JPEG still on the rising edge of motion detection.

Both are driven from CameraProducer.  Usage:

    recorder = CameraRecorder(cam_index, config)
    snapshotter = MotionSnapshot(cam_index, config)

    # in capture loop:
    recorder.write(raw_frame)
    snapshotter.on_frame(raw_frame, motion_detected)
"""

import cv2
import os
import time
import threading
import datetime
import logging

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Motion snapshots
# ---------------------------------------------------------------------------

class MotionSnapshot:
    """
    Saves a JPEG still photo when motion is first detected (rising edge only –
    one photo per motion event, not one per frame).

    Files are saved to:  <storage_path>/snapshots/cam{n}_YYYYMMDD_HHMMSS.jpg
    """

    def __init__(self, cam_index: int, config):
        self.cam_index = cam_index
        self.config = config
        self._was_motion = False      # motion state from the previous frame
        self._lock = threading.Lock()

    def on_frame(self, frame, motion_detected: bool) -> None:
        """
        Call with every raw BGR frame and the current motion flag.
        A JPEG is written only on the rising edge (False -> True transition).
        """
        if not self.config.motion_detection:
            return

        with self._lock:
            rising_edge = motion_detected and not self._was_motion
            self._was_motion = motion_detected

        if not rising_edge:
            return

        snap_dir = os.path.join(self.config.storage_path, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cam{self.cam_index}_{ts}.jpg"
        path = os.path.join(snap_dir, filename)

        ok, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if ok:
            with open(path, "wb") as fh:
                fh.write(jpeg.tobytes())
            log.info(f"[Snapshot cam{self.cam_index}] Motion detected - saved {filename}")
        else:
            log.warning(f"[Snapshot cam{self.cam_index}] Failed to encode JPEG")


# ---------------------------------------------------------------------------
# Rolling video recorder
# ---------------------------------------------------------------------------

class CameraRecorder:
    """
    Writes rolling MP4 recordings for one camera.

      - Each clip is `recording_length` minutes long (from config).
      - Files are named  cam{n}_YYYYMMDD_HHMMSS.mp4  under `storage_path`.
      - A background thread runs every hour and deletes clips older than
        `video_retention` days.  Set video_retention=0 to keep forever.
    """

    def __init__(self, cam_index: int, config):
        self.cam_index = cam_index
        self.config = config

        self._writer = None
        self._clip_start = 0.0
        self._clip_path = ""
        self._frame_count = 0

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._cleanup_thread = threading.Thread(
            target=self._retention_loop, daemon=True,
            name=f"recorder-cleanup-{cam_index}"
        )
        self._cleanup_thread.start()

    def write(self, frame) -> None:
        """Accept a raw BGR frame. Opens / rolls clips automatically."""
        if not self.config.record:
            return

        with self._lock:
            now = time.time()
            if self._writer is None or (now - self._clip_start) >= self.config.recording_length * 60:
                self._open_new_clip(frame)

            if self._writer and self._writer.isOpened():
                self._writer.write(frame)
                self._frame_count += 1

    def stop(self) -> None:
        """Flush and close the current clip cleanly."""
        self._stop_event.set()
        with self._lock:
            self._close_clip()

    def _open_new_clip(self, frame) -> None:
        self._close_clip()

        storage = self.config.storage_path
        os.makedirs(storage, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cam{self.cam_index}_{ts}.mp4"
        self._clip_path = os.path.join(storage, filename)

        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(
            self._clip_path, fourcc, self.config.camera_fps, (w, h)
        )

        if not self._writer.isOpened():
            log.error(f"[Recorder cam{self.cam_index}] Failed to open {self._clip_path}")
            self._writer = None
            return

        self._clip_start = time.time()
        self._frame_count = 0
        log.info(f"[Recorder cam{self.cam_index}] New clip: {filename}")

    def _close_clip(self) -> None:
        if self._writer is not None:
            self._writer.release()
            log.info(
                f"[Recorder cam{self.cam_index}] Closed {os.path.basename(self._clip_path)} "
                f"({self._frame_count} frames)"
            )
            self._writer = None
            self._frame_count = 0

    def _retention_loop(self) -> None:
        while not self._stop_event.is_set():
            self._delete_old_clips()
            for _ in range(60):
                if self._stop_event.wait(timeout=60):
                    return

    def _delete_old_clips(self) -> None:
        retention_days = self.config.video_retention
        if retention_days <= 0:
            return

        storage = self.config.storage_path
        if not os.path.isdir(storage):
            return

        cutoff = time.time() - retention_days * 86400
        deleted = 0
        for fname in os.listdir(storage):
            if not fname.endswith(".mp4"):
                continue
            fpath = os.path.join(storage, fname)
            try:
                if os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
                    deleted += 1
            except OSError as exc:
                log.warning(f"[Recorder] Could not delete {fpath}: {exc}")

        if deleted:
            log.info(f"[Recorder cam{self.cam_index}] Deleted {deleted} old clip(s)")