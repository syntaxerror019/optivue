"""
frame_buffer.py  –  utils/frame_buffer.py

Replaces named pipes with a thread-safe in-memory frame store.

Each camera gets one FrameBuffer instance. The producer writes the latest
JPEG bytes into it; any number of streaming clients read from it independently
via `subscribe()`, which returns a generator that yields new frames as they
arrive.  No byte-splitting, no race conditions.
"""

import threading
import time
from typing import Optional


class FrameBuffer:
    """
    Holds the most-recent JPEG frame for one camera.

    Clients never compete for bytes – they each get their own copy of every
    frame via a Condition-based subscription.
    """

    def __init__(self, cam_index: int):
        self.cam_index = cam_index
        self._frame: Optional[bytes] = None
        self._lock = threading.Condition()
        self._frame_number: int = 0          # increments on every new frame
        self._closed: bool = False

    # ------------------------------------------------------------------
    # Producer side
    # ------------------------------------------------------------------

    def push(self, jpeg_bytes: bytes) -> None:
        """Called by CameraProducer each time a new JPEG is ready."""
        with self._lock:
            self._frame = jpeg_bytes
            self._frame_number += 1
            self._lock.notify_all()          # wake all waiting subscribers

    def close(self) -> None:
        """Signal all subscribers that the stream has ended."""
        with self._lock:
            self._closed = True
            self._lock.notify_all()

    # ------------------------------------------------------------------
    # Consumer side
    # ------------------------------------------------------------------

    def subscribe(self, timeout: float = 5.0):
        """
        Generator that yields (frame_number, jpeg_bytes) for every new frame.

        Each caller gets its own independent cursor so multiple clients never
        interfere with each other.  Yields `None` on timeout so the caller can
        check liveness and bail out if the client has disconnected.
        """
        last_seen = -1
        while True:
            with self._lock:
                # Wait until there is a frame we haven't seen yet
                deadline = time.monotonic() + timeout
                while self._frame_number == last_seen and not self._closed:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        yield None          # timeout – let caller decide
                        deadline = time.monotonic() + timeout
                        continue
                    self._lock.wait(timeout=remaining)

                if self._closed:
                    return

                last_seen = self._frame_number
                frame = self._frame

            yield frame

    @property
    def latest(self) -> Optional[bytes]:
        """Return the most-recent frame without blocking (may be None)."""
        return self._frame


# ------------------------------------------------------------------
# Registry – one global dict indexed by camera index
# ------------------------------------------------------------------

_registry: dict[int, FrameBuffer] = {}
_registry_lock = threading.Lock()


def get_or_create(cam_index: int) -> FrameBuffer:
    with _registry_lock:
        if cam_index not in _registry:
            _registry[cam_index] = FrameBuffer(cam_index)
        return _registry[cam_index]


def get(cam_index: int) -> Optional[FrameBuffer]:
    return _registry.get(cam_index)


def all_buffers() -> dict[int, FrameBuffer]:
    with _registry_lock:
        return dict(_registry)