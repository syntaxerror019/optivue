import yaml
import os

class ConfigLoader:
    _instance = None  # single  ton to not reloading

    def __new__(cls, config_file="config.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(config_file)
        return cls._instance

    def _load(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_file, "r") as f:
            cfg = yaml.safe_load(f)

        camera_cfg = cfg.get("camera", {})
        self.camera_width = camera_cfg.get("width", 640)
        self.camera_height = camera_cfg.get("height", 480)
        self.camera_fps = camera_cfg.get("fps", 15)
        self.motion_contour_area = camera_cfg.get("motion_contour_area", 500)

        #Pipe settings
        pipes_cfg = cfg.get("pipes", {})
        self.pipes_dir = pipes_cfg.get("dir", "/tmp/cam_pipes")

        server_cfg = cfg.get("server", {})
        self.server_host = server_cfg.get("host", "0.0.0.0")
        self.server_port = server_cfg.get("port", 5000)

    def __repr__(self):
        return (f"<ConfigLoader camera={self.camera_width}x{self.camera_height}@{self.camera_fps}fps, "
                f"motion_area={self.motion_contour_area}, pipes_dir={self.pipes_dir}>")
