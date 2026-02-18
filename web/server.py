"""
server.py  –  web/server.py

Flask streaming server.  Each client that hits /stream/<name> gets its own
independent generator pulling from a FrameBuffer – no shared byte-stream,
no corruption when multiple browsers connect simultaneously.
"""

import os
import time
import threading
import logging

from flask import Flask, Response, render_template, request
from web.auth import require_basic_auth
from utils.config import ConfigSaver
from utils import frame_buffer as fb

log = logging.getLogger(__name__)


class StreamingServer:
    def __init__(self, pipe_dir=None, host="0.0.0.0", port=5000, config=None):
        # pipe_dir kept for API compatibility but is no longer used
        self.config = config
        self.host = host
        self.port = port

        self.app = Flask(__name__)
        self.routes_created: list[dict] = []
        self.config_saver = ConfigSaver()

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Static routes
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/settings", "settings", self.settings, methods=["GET", "POST"])

    # ------------------------------------------------------------------
    # MJPEG streaming  (one generator instance per connected client)
    # ------------------------------------------------------------------

    def _generate_mjpeg(self, cam_index: int):
        """
        Generator that yields multipart MJPEG chunks.

        Runs entirely inside the client's request thread; uses FrameBuffer
        .subscribe() (I want to try PUBSUB approach here) which is a blocking iterator that wakes on each new frame.
        Because every caller gets its own independent cursor, simultaneous viewers never interfere with each other.
        """
        buf = fb.get(cam_index)
        if buf is None:
            return

        for jpeg_bytes in buf.subscribe(timeout=5.0):
            if jpeg_bytes is None:
                # Timeout heartbeat – generator will be garbage collected
                # automatically when the client disconnects
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg_bytes
                + b"\r\n"
            )

    def _make_stream_route(self, cam_index: int):
        def stream_view():
            return Response(
                self._generate_mjpeg(cam_index),
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )
        return stream_view

    # ------------------------------------------------------------------
    # Route registration  (called after producers have started)
    # ------------------------------------------------------------------

    def add_routes(self):
        for cam_index, buf in fb.all_buffers().items():
            route_path = f"/stream/cam{cam_index}.mjpeg"
            endpoint   = f"stream_cam{cam_index}"

            self.app.add_url_rule(
                route_path, endpoint, self._make_stream_route(cam_index)
            )

            self.routes_created.append({
                "name":       f"cam{cam_index}.mjpeg",
                "url":        route_path,
                "resolution": f"{self.config.camera_width}x{self.config.camera_height}",
                "framerate":  self.config.camera_fps,
                "show_info":  True,
            })
            log.info(f"Streaming route registered: {route_path}")

    # ------------------------------------------------------------------
    # Page routes
    # ------------------------------------------------------------------

    # Uncomment the decorator below to enable HTTP Basic Auth:
    # @require_basic_auth
    def index(self):
        return render_template(
            "index.html",
            cameras=self.routes_created,
            page="live",
            page_title="Live View",
            status_text="Connected",
        )

    def settings(self):
        if request.method == "GET":
            return render_template(
                "settings.html",
                page="settings",
                page_title="Settings",
                status_text="Connected",
                config=self.config,
            )

        # POST – save JSON settings and trigger config reload
        data = request.get_json()
        if not data:
            return "Bad request", 400

        try:
            self.config_saver.save(
                **{
                    "camera.width":               int(data["resolution"].split("x")[0]),
                    "camera.height":              int(data["resolution"].split("x")[1]),
                    "camera.fps":                 int(data["frameRate"]),
                    "camera.motion_detection":    bool(data["motionDetection"]),
                    "camera.motion_contour_area": int(data["sensitivity"]),
                    "record.enabled":             bool(data["record"]),
                    "record.recording_length":    int(data["recordingLength"]),
                    "record.storage_path":        data["storagePath"],
                    "record.video_retention":     int(data["videoRetention"]),
                }
            )
        except (KeyError, ValueError) as exc:
            log.error(f"Settings save error: {exc}")
            return f"Invalid data: {exc}", 400

        return "ok", 200

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    def start(self):
        self.add_routes()
        log.info(f"Starting server on http://{self.host}:{self.port}")

        def run():
            # use_reloader=False is required when running inside a thread
            self.app.run(
                host=self.host,
                port=self.port,
                threaded=True,
                use_reloader=False,
            )

        self._thread = threading.Thread(target=run, daemon=True, name="flask-server")
        self._thread.start()

    def stop(self):
        # Flask's dev server has no clean shutdown via thread;
        # since the thread is daemonised it dies with the process.
        # For production, swap app.run() for a Werkzeug/Waitress server.
        self._stop_event.set()
        log.info("StreamingServer stop requested.")