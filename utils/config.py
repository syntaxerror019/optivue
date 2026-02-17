import yaml
import os
import threading

class ConfigLoader:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_file="config.yaml"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.config_file = config_file
                cls._instance._refresh_requested = False
                cls._instance._load()
        return cls._instance

    def _load(self):
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(self.config_file)

        with open(self.config_file) as f:
            cfg = yaml.safe_load(f) or {}

        # Cameras
        self.cameras = [int(c) for c in cfg.get("cameras", [0])]

        camera = cfg.get("camera", {})
        self.camera_width = camera.get("width", 640)
        self.camera_height = camera.get("height", 480)
        self.camera_fps = camera.get("fps", 15)
        self.compression = camera.get("compression", "mjpeg")
        self.motion_detection = camera.get("motion_detection", True)
        self.motion_contour_area = camera.get("motion_contour_area", 500)

        record = cfg.get("record", {})
        self.record = record.get("enabled", True)
        self.recording_length = record.get("recording_length", 60)
        self.storage_path = record.get("storage_path", "/var/optivue/recordings")
        self.video_retention = record.get("video_retention", 30)

        pipes = cfg.get("pipes", {})
        self.pipes_dir = pipes.get("dir", "/tmp/cam_pipes")

        server = cfg.get("server", {})
        self.server_host = server.get("host", "0.0.0.0")
        self.server_port = server.get("port", 5000)

        self._refresh_requested = False

    def request_refresh(self):
        self._refresh_requested = True
        
    def clear_refresh(self):
        self._refresh_requested = False

    def check_refresh(self):
        return self._refresh_requested

    def reload(self):
        self._load()

    def __repr__(self):
        return (
            f"<ConfigLoader "
            f"{self.camera_width}x{self.camera_height}@{self.camera_fps}fps "
            f"motion_area={self.motion_contour_area}>"
        )

class ConfigSaver:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file

    def save(self, **paths):
        with open(self.config_file) as f:
            config = yaml.safe_load(f) or {}

        for path, value in paths.items():
            keys = path.split(".")
            d = config
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            d[keys[-1]] = value

        with open(self.config_file, "w") as f:
            yaml.safe_dump(config, f)
            
        ConfigLoader().request_refresh()
