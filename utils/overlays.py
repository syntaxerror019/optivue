import cv2
import time

# Cache font and other constants
_FONT = cv2.FONT_HERSHEY_SIMPLEX
_SCALE = 0.5
_TEXT_THICKNESS = 1
_TEXT_COLOR = (255, 255, 255)
_BG_COLOR = (0, 0, 0)

# Global cache for overlay rendering (one per camera)
_overlay_cache = {}

def add_overlay(frame, cam_index, motion_detected=False):
    """Ultra-optimized overlay with caching"""
    
    # Initialize cache for this camera if needed
    if cam_index not in _overlay_cache:
        _overlay_cache[cam_index] = {
            'last_second': -1,
            'last_motion': None,
            'overlay_region': None
        }
    
    cache = _overlay_cache[cam_index]
    current_second = int(time.time())
    
    # Only redraw if second changed or motion state changed
    if (current_second != cache['last_second'] or 
        motion_detected != cache['last_motion']):
        
        timestamp = time.strftime("%H:%M:%S")
        status = "MOTION" if motion_detected else "OK    "
        text = f"C{cam_index} {timestamp} {status}"
        
        # Get text size
        text_size = cv2.getTextSize(text, _FONT, _SCALE, _TEXT_THICKNESS)[0]
        
        # Create small overlay region (just the text area)
        org = (5, 20)
        overlay_height = text_size[1] + 8
        overlay_width = text_size[0] + 8
        overlay = frame[0:overlay_height, 0:overlay_width].copy()
        
        # Draw background rectangle on overlay region
        cv2.rectangle(overlay,
                     (3, 3),
                     (overlay_width - 3, overlay_height - 3),
                     _BG_COLOR, -1)
        
        # Draw text on overlay region
        cv2.putText(overlay, text, (5, text_size[1] + 5), _FONT, 
                   _SCALE, _TEXT_COLOR, _TEXT_THICKNESS)
        
        # Cache the overlay region
        cache['overlay_region'] = overlay
        cache['last_second'] = current_second
        cache['last_motion'] = motion_detected
    
    # Apply cached overlay to frame (very fast blit operation)
    if cache['overlay_region'] is not None:
        h, w = cache['overlay_region'].shape[:2]
        frame[0:h, 0:w] = cache['overlay_region']
    
    return frame