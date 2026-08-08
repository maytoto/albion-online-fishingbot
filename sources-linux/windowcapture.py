import subprocess
import numpy as np
import pyautogui

class WindowCapture:

    def __init__(self, window_class):
        self.hwnd = self.find_window_by_title(window_class)
        if not self.hwnd:
            raise Exception(f"Window not found with class: {window_class}")

        # Get window geometry using xdotool
        window_geometry = subprocess.run(
            ["xdotool", "getwindowgeometry", "--shell", self.hwnd],
            capture_output=True,
            text=True
        ).stdout
        geometry_info = dict(line.split('=') for line in window_geometry.splitlines() if '=' in line)
        self.x = int(geometry_info['X'])
        self.y = int(geometry_info['Y'])
        self.w = int(geometry_info['WIDTH'])
        self.h = int(geometry_info['HEIGHT'])

        # Offset for window borders (if necessary, depends on your environment)
        self.offset_x = self.x
        self.offset_y = self.y

    def find_window_by_title(self, partial_class):
    # Use xdotool to search for windows by class
        try:
            result = subprocess.run(
                ["xdotool", "search", "--class", partial_class],
                capture_output=True,
                text=True
            )
            window_ids = result.stdout.splitlines()
            if window_ids:
                return window_ids[0]  # Return the first matching window ID
            else:
                print(f"No windows found with class: {partial_class}")
                return None
        except Exception as e:
            print(f"Error finding window: {e}")
            return None
    def activate_window(self, window_id):
        subprocess.run(["xdotool", "windowactivate", window_id])

    def get_screenshot(self, region=None):
        # Use pyautogui to capture a screenshot of the specified region
        if region:
            region_x = self.offset_x + region[0]
            region_y = self.offset_y + region[1]
            region_width = region[2]
            region_height = region[3]
        else:
            region_x, region_y, region_width, region_height = self.offset_x, self.offset_y, self.w, self.h

        im = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
        return np.array(im)[..., :3]  # Drop alpha channel
