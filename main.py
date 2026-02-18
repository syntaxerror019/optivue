"""
main.py

Entry point.  Starts one CameraProducer per configured camera, then
starts the Flask streaming server.  Waits for a config-reload signal,
then tears everything down and restarts.
"""

import os
import time
import threading
import logging

from stream.produce import CameraProducer
from utils.config import ConfigLoader
from utils.restart import restart_script
from web.server import StreamingServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def main():
    os.nice(0)

    while True:
        config = ConfigLoader()
        config.clear_refresh()

        # Start one producer per camera
        producers = []
        for cam_index in config.cameras:
            p = CameraProducer(
                cam_index,
                width=config.camera_width,
                height=config.camera_height,
                fps=config.camera_fps,
                motion_area=config.motion_contour_area,
                config=config,
            )
            p.start()
            producers.append(p)

        # Give producers a moment to register their FrameBuffers
        time.sleep(0.2)

        # Start the web server
        server = StreamingServer(
            host=config.server_host,
            port=config.server_port,
            config=config,
        )
        server.start()

        # Wait until a settings save triggers a reload
        try:
            while not config.check_refresh():
                time.sleep(0.5)
        except KeyboardInterrupt:
            log.info("Interrupted... shutting down.")
            break

        log.info("Config reload requested ...restarting...")

        for p in producers:
            p.stop()
        server.stop()

        restart_script()


if __name__ == "__main__":
    main()