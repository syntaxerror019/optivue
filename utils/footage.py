import os
import datetime
import logging
from collections import defaultdict

log = logging.getLogger(__name__)

class Footage:
    """
    Scans storage for MP4 and JPEG files, parses timestamps from filenames like:
    cam0_YYYYMMDD_HHMMSS.mp4 or cam0_YYYYMMDD_HHMMSS.jpg
    Returns media grouped by camera.
    """

    def __init__(self, storage_path):
        self.storage_path = storage_path
        print(f"Footage initialized with storage path: {storage_path}")

    def _parse_filename(self, fname):
        """
        Extracts camera and timestamp from filename.
        Format: camX_YYYYMMDD_HHMMSS.ext
        """
        try:
            base, ext = os.path.splitext(fname)
            cam, ts_str = base.split("_", 1)  # split at first underscore
            ts = datetime.datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            return cam, ts
        except Exception as e:
            log.warning(f"Failed to parse timestamp from {fname}: {e}")
            return None, None

    def _scan_dir(self, directory, ext):
        media_map = defaultdict(list)
        if not os.path.isdir(directory):
            return media_map

        for fname in os.listdir(directory):
            if fname.endswith(ext) and fname.startswith("cam"):
                cam, ts = self._parse_filename(fname)
                if cam and ts:
                    media_map[cam].append({"filename": fname, "timestamp": ts})

        # sort descending
        for cam in media_map:
            media_map[cam].sort(key=lambda x: x["timestamp"], reverse=True)
        return media_map

    def get_clips(self):
        return self._scan_dir(self.storage_path, ".mp4")

    def get_snapshots(self):
        snap_dir = os.path.join(self.storage_path, "snapshots")
        return self._scan_dir(snap_dir, ".jpg")

    def get_all_media(self):
        """
        Returns combined structure for Jinja:
        {
            cam0: {clips: [...], snapshots: [...]},
            cam1: {clips: [...], snapshots: [...]},
        }
        """
        clips = self.get_clips()
        snaps = self.get_snapshots()
        cameras = {}
        all_cams = set(list(clips.keys()) + list(snaps.keys()))
        for cam in all_cams:
            cameras[cam] = {
                "clips": clips.get(cam, []),
                "snapshots": snaps.get(cam, [])
            }
        return cameras
