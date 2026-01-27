from stream.produce import CameraProducer
from utils.config import ConfigLoader
from utils.indices import detect_cameras
from web.server import StreamingServer

def main():
    config = ConfigLoader()

    #get cameras
    camera_indices = detect_cameras()
    
    print(f"Detected cameras: {camera_indices}")

    producers = []
    for cam_index in camera_indices:
        producer = CameraProducer(
            cam_index,
            pipe_dir=config.pipes_dir,
            width=config.camera_width,
            height=config.camera_height,
            fps=config.camera_fps,
            motion_area=config.motion_contour_area
        )
        producer.start()
        producers.append(producer)
        
    server = StreamingServer(
        pipe_dir=config.pipes_dir,
        host=config.server_host,
        port=config.server_port
    )
    
    server.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        for producer in producers:
            producer.stop()

if __name__ == "__main__":
    main()
