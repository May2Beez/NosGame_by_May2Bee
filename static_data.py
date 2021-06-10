import os
import sys

import numpy as np
from PIL import Image


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Check if RGB value is on image (for checking if Bat is over bob)
def detect_color(rgb, img):
    pix = Image.fromarray(np.uint8(img)).convert('RGB')

    pix = pix.load()

    for y in range(0, img.shape[0]):
        for x in range(0, img.shape[1]):
            if pix[x, y] in rgb:
                return True
    return False


class StaticData:
    reward_positions = [(), (374, 435), (442, 435), (510, 435), (578, 435), (646, 435)]
    result_window_rgb = [(247, 168, 150), ]
    get_reward_position = (640, 435)
    stop_position = (564, 465)
    try_again_position = (455, 465)
    try_again_after_fail_or_end_position = (379, 435)
