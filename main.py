from stream.produce import CameraProducer
from utils.config import ConfigLoader
from utils.restart import restart_script
from web.server import StreamingServer
import threading
import os
import time
def main():
    os.nice(0)

    while True:
        config = ConfigLoader()
        
        config.clear_refresh()

        producers = []
        for cam_index in config.cameras:
            p = CameraProducer(
                cam_index,
                pipe_dir=config.pipes_dir,
                width=config.camera_width,
                height=config.camera_height,
                fps=config.camera_fps,
                motion_area=config.motion_contour_area,
                config=config,
            )
            p.start()
            producers.append(p)

        server = StreamingServer(
            pipe_dir=config.pipes_dir,
            host=config.server_host,
            port=config.server_port,
            config=config,
        )
        server.start()

        # 🔁 Wait until refresh requested
        try:
            while not config.check_refresh():
                time.sleep(0.5)
        except KeyboardInterrupt:
            break

        print("🔄 Reloading config...")

        # Stop everything cleanly
        for p in producers:
            p.stop()
        server.stop()

        restart_script()

if __name__ == "__main__":
    main()
