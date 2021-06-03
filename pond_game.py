import os
import sys
import time
import cv2
from threading import Thread

from PIL import Image
import numpy as np

import win32api
import win32con
import win32gui

import vision
import WindowCapture
import check_score


# Get images directory
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

    for x in range(0, img.shape[1] - 1):
        for y in range(0, img.shape[0] - 1):
            if pix[x, y] in rgb:
                return True
    return False


class PondGame:
    def __init__(self, NosTale_name, repeats, level):
        self.NosTale_hwnd = win32gui.FindWindow('TNosTaleMainF', NosTale_name)
        self.NosTale_name = NosTale_name
        self.NosTale_window = WindowCapture.WindowCapture(window_hwnd=self.NosTale_hwnd)
        self.start_pond = vision.Vision(cv2.imread(resource_path("images/start_pond.png")))
        self.score_checker = check_score.CheckScore(
            cv2.imread(resource_path("images/score_digits.png"), cv2.IMREAD_GRAYSCALE))
        self.bat_pixel_rgb = [(2, 0, 3), (2, 2, 4)]
        self.playing = False
        self.failed = False
        self.window_rect = win32gui.GetWindowRect(self.NosTale_hwnd)
        self.window_h = self.window_rect[3] - self.window_rect[1]
        self.window_w = self.window_rect[2] - self.window_rect[0]
        self.reward_level = level
        self.repeats = repeats
        self.repeats_counter = 1
        self.score_levels = [0, 1000, 4000, 8000, 12000, 20000]
        self.if_pond_start_exists()

    def checking_score_thread(self):

        while self.playing:

            try:

                img = self.NosTale_window.get_screenshot()

            except Exception:
                continue

            score_img_x = int(img.shape[1] / 2 - 181)
            score_img_y = int(img.shape[0] / 2 - 198)

            score_img = img[score_img_y:(score_img_y + 26), score_img_x:(score_img_x + 220)]

            score = self.score_checker.check_score(score_img)

            if score > int(self.score_levels[int(self.reward_level)]):
                self.playing = False
                self.failed = False

    # Checks if game window is opened
    def if_pond_start_exists(self):
        start = time.time()
        while not self.playing:
            print("[" + str(self.NosTale_name) + "] Searching for start button...")
            img = WindowCapture.WindowCapture(window_hwnd=self.NosTale_hwnd).get_screenshot()
            self.points = self.start_pond.find(img, threshold=0.9)
            if time.time() - start > 5:
                print("[" + str(self.NosTale_name) + "] I coudn't find start within 5 seconds")
                break
            if self.points:
                print("[" + str(self.NosTale_name) + "] Found start button")
                self.playing = True
                self.failed = False
                self.click_pond_start()
                break

            time.sleep(1)

    # Clicks start game
    def click_pond_start(self):
        print(
            "[" + str(self.NosTale_name) + "] Doing " + str(self.repeats_counter) + "/" + str(self.repeats) + " repeat")
        lParam = win32api.MAKELONG(self.points[0][0], self.points[0][1] + 20)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
        time.sleep(1)
        self.find_bobs()

    # Defines images to variables and starts game
    def find_bobs(self):
        self.left_bot_bob = vision.Vision(cv2.imread(resource_path("images/bob_left_bot.png")))
        self.right_top_bob = vision.Vision(cv2.imread(resource_path("images/bob_top_right.png")))
        self.result_window = vision.Vision(cv2.imread(resource_path("images/result_window.png")))
        self.get_reward = vision.Vision(cv2.imread(resource_path("images/get_reward.png")))

        if self.left_bot_bob and self.right_top_bob:
            time.sleep(0.1)
            self.play_game()

    # Single click of key with delay
    def click(self, key, delay=True):
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, key, 0x002C0001)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, key, 0xC02C0001)
        if delay:
            time.sleep(0.75)

    # Checks if bat is over bob
    def check_bat_over_bob(self, img, the_way, key):
        search_bat = img[int(the_way[1] - 25):int(the_way[1] - 10), int(the_way[0] - 15):int(the_way[0] + 5)].copy()

        if not detect_color(self.bat_pixel_rgb, search_bat):
            self.click(key)

    # Main functionality
    def play_game(self):
        combo_fish = vision.Vision(cv2.imread(resource_path("images/combo_fish.png")))
        img = self.NosTale_window.get_screenshot()

        x = img.shape[1] / 2 - 350 / 2
        y = img.shape[0] / 2 - 200 / 2
        bobs = img[int(y):int(y + 200), int(x):int(x + 350)].copy()

        while True:
            not_moving_left, not_moving_bot = self.left_bot_bob.find(bobs, threshold=0.95)
            not_moving_top, not_moving_right = self.right_top_bob.find(bobs, threshold=0.95)

            if not_moving_left and not_moving_bot and not_moving_right and not_moving_top:
                break

        self.score = Thread(target=self.checking_score_thread, args=())
        self.score.start()

        while self.playing:

            # IMG for checking if fish catches
            try:
                img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            x = img.shape[1] / 2 - 350 / 2
            y = img.shape[0] / 2 - 200 / 2
            bobs = img[int(y):int(y + 200), int(x):int(x + 350)].copy()

            # IMG for game window
            crop_x = img.shape[1] / 2 - 550 / 2
            crop_y = img.shape[0] / 2 - 480 / 2
            game_img = img[int(crop_y):int(crop_y + 480), int(crop_x):int(crop_x + 550)].copy()

            # IMG for combo fish
            combo_x = game_img.shape[1] / 2 - 500 / 2
            combo_y = game_img.shape[0] / 2 - 100 / 2
            combo_fish_crop_img = game_img[int(combo_y):int(combo_y + 100), int(combo_x):int(combo_x + 500)].copy()

            if combo_fish.find(combo_fish_crop_img, threshold=0.90):

                self.solve_combo_fish()
                time.sleep(1)

            else:

                left_bot = self.left_bot_bob.find(bobs, threshold=0.90)

                if not_moving_left not in left_bot or not_moving_bot not in left_bot:

                    if not_moving_left not in left_bot:

                        self.check_bat_over_bob(bobs, not_moving_left, win32con.VK_LEFT)

                    elif not_moving_bot not in left_bot:

                        self.check_bat_over_bob(bobs, not_moving_bot, win32con.VK_DOWN)

                else:

                    right_top = self.right_top_bob.find(bobs, threshold=0.90)

                    if not_moving_top not in right_top:

                        self.check_bat_over_bob(bobs, not_moving_top, win32con.VK_UP)

                    elif not_moving_right not in right_top:

                        self.check_bat_over_bob(bobs, not_moving_right, win32con.VK_RIGHT)

                # Full IMG
                try:
                    fail_img = self.NosTale_window.get_screenshot()
                except Exception:
                    continue

                # IMG for result window
                result_window_x = fail_img.shape[1] / 2 - 400 / 2
                result_window_y = fail_img.shape[0] / 2 - 200 / 2
                result_window_crop_img = fail_img[int(result_window_y):int(result_window_y + 200),
                                         int(result_window_x):int(result_window_x + 400)].copy()

                if self.result_window.find(result_window_crop_img, threshold=0.90):
                    self.failed = True
                    self.playing = False
                    break

            #time.sleep(0.1)

        time.sleep(0.1)

        if not self.playing:
            self.stop_game()

    # Check end
    def stop_game(self):
        self.score.join()

        if not self.failed:

            while not self.failed:

                try:
                    img = self.NosTale_window.get_screenshot()
                except Exception:
                    continue

                # IMG for game window
                crop_x = img.shape[1] / 2 - 550 / 2
                crop_y = img.shape[0] / 2 - 480 / 2
                game_img = img[int(crop_y):int(crop_y + 480), int(crop_x):int(crop_x + 550)].copy()

                # IMG for result window
                result_window_x = game_img.shape[1] / 2 - 400 / 2
                result_window_y = game_img.shape[0] / 2 - 200 / 2
                result_window_crop_img = game_img[int(result_window_y):int(result_window_y + 200),
                                         int(result_window_x):int(result_window_x + 400)].copy()

                if self.result_window.find(result_window_crop_img, threshold=0.90):
                    break

                self.click(win32con.VK_LEFT, False)

                time.sleep(0.5)

            while True:

                reward_points = self.get_reward.find(img, threshold=0.95)

                if reward_points:
                    break

                time.sleep(0.1)

            # Click Reward button
            lParam = win32api.MAKELONG(reward_points[0][0], reward_points[0][1] + 20)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(1.5)

            # Click level reward
            reward_button_y = int(img.shape[0] / 2 + 50)
            reward_button_x = int(
                (img.shape[1] / 2 + (int(self.reward_level) - 3) * 70) if int(self.reward_level) >= 3 else (
                        img.shape[0] / 2 - (int(self.reward_level) - 3) * 70))

            lParam = win32api.MAKELONG(reward_button_x, reward_button_y)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(1.5)

            self.repeats_counter += 1

            finish_img = self.NosTale_window.get_screenshot()

            if self.repeats_counter <= self.repeats:

                options_to_choose = vision.Vision(cv2.imread(resource_path("images/try_again.png")))

            else:

                options_to_choose = vision.Vision(cv2.imread(resource_path("images/end_session.png")))
                print("[" + str(self.NosTale_name) + "] Has finished all repeats")

            while True:

                chosen_option_points = options_to_choose.find(finish_img, threshold=0.85)

                if chosen_option_points:
                    break

            time.sleep(0.1)

            lParam = win32api.MAKELONG(chosen_option_points[0][0], chosen_option_points[0][1] + 20)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(1.5)

            end_img = self.NosTale_window.get_screenshot()

            # IMG for result window
            result_window_x = end_img.shape[1] / 2 - 400 / 2
            result_window_y = end_img.shape[0] / 2 - 200 / 2
            result_window_crop_img = end_img[int(result_window_y):int(result_window_y + 200),
                                     int(result_window_x):int(result_window_x + 400)].copy()

            if vision.Vision(cv2.imread(resource_path("images/not_enough_points.png"))).find(result_window_crop_img,
                                                                                             threshold=0.9):

                print("[" + str(self.NosTale_name) + "] Not enough points to play")

                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0x002C0001)
                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0xC02C0001)

                time.sleep(0.1)

                end_img = self.NosTale_window.get_screenshot()

                options_to_choose = vision.Vision(cv2.imread(resource_path("images/end_session.png")))

                chosen_option_points = options_to_choose.find(end_img, threshold=0.92)

                time.sleep(0.1)

                lParam = win32api.MAKELONG(chosen_option_points[0][0], chosen_option_points[0][1] + 20)
                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
                time.sleep(1)

            elif self.repeats_counter <= self.repeats:

                self.if_pond_start_exists()

        else:
            time.sleep(0.1)

            try_again_btn_y = (self.window_h / 2) + 30
            try_again_btn_x = (self.window_w / 2) - 100

            lParam = win32api.MAKELONG(int(try_again_btn_x), int(try_again_btn_y))
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(1)

            print("[" + str(self.NosTale_name) + "] Bot failed and will try again")

            self.if_pond_start_exists()

    # Solving combo fish
    def solve_combo_fish(self):
        arrow_left = vision.Vision(cv2.imread(resource_path("images/arrow_left.bmp")))
        arrow_up = vision.Vision(cv2.imread(resource_path("images/arrow_up.bmp")))
        arrow_right = vision.Vision(cv2.imread(resource_path("images/arrow_right.bmp")))
        arrow_down = vision.Vision(cv2.imread(resource_path("images/arrow_down.bmp")))

        combo = 0

        start = time.time()

        while combo < 8 and time.time() - start <= 3.5:
            try:
                img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            x = img.shape[1] / 2 - 500 / 2
            y = img.shape[0] / 2 - 420 / 2
            crop_img = img[int(y):int(y + 420), int(x):int(x + 500)].copy()

            if arrow_left.find(crop_img, threshold=0.98):
                self.click(win32con.VK_LEFT, False)
                combo += 1

            if arrow_up.find(crop_img, threshold=0.98):
                self.click(win32con.VK_UP, False)
                combo += 1

            if arrow_right.find(crop_img, threshold=0.98):
                self.click(win32con.VK_RIGHT, False)
                combo += 1

            if arrow_down.find(crop_img, threshold=0.98):
                self.click(win32con.VK_DOWN, False)
                combo += 1

        time.sleep(0.2)
