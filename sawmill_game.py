import os
import sys
import time
import cv2
from threading import Thread

import win32api
import win32con
import win32gui

import check_score
import vision
import WindowCapture


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Sawmill:
    def __init__(self, NosTale_name, repeats, level):
        self.NosTale_hwnd = win32gui.FindWindow('TNosTaleMainF', NosTale_name)
        self.NosTale_name = NosTale_name
        self.NosTale_window = WindowCapture.WindowCapture(window_hwnd=self.NosTale_hwnd)
        self.start_sawmill = vision.Vision(cv2.imread(resource_path("images/start_sawmill.png")))
        self.score_checker = check_score.CheckScore(
            cv2.imread(resource_path("images/score_digits.png"), cv2.IMREAD_GRAYSCALE))
        self.repeats = repeats
        self.repeats_counter = 1
        self.reward_level = level
        self.score_levels = [0, 1000, 5000, 10000, 14000, 18000]
        self.playing = False
        self.failed = False
        self.window_rect = win32gui.GetWindowRect(self.NosTale_hwnd)
        self.window_h = self.window_rect[3] - self.window_rect[1]
        self.window_w = self.window_rect[2] - self.window_rect[0]
        self.if_sawmill_start_exists()

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

    def if_sawmill_start_exists(self):
        start = time.time()
        while not self.playing:
            print("[" + str(self.NosTale_name) + "] Searching for start button...")
            img = WindowCapture.WindowCapture(window_hwnd=self.NosTale_hwnd).get_screenshot()
            points = self.start_sawmill.find(img, threshold=0.9)
            if time.time() - start > 5:
                print("[" + str(self.NosTale_name) + "] I coudn't find start within 5 seconds")
                break
            if points:
                print("[" + str(self.NosTale_name) + "] Found start button")
                print("[" + str(self.NosTale_name) + "] Doing " + str(self.repeats_counter) + "/" + str(
                        self.repeats) + " repeat")

                self.playing = True
                self.click_sawmill_start(points)

            time.sleep(1)

    def click(self, key):
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, key, 0x002C0001)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, key, 0xC02C0001)

    def click_sawmill_start(self, points):
        lParam = win32api.MAKELONG(points[0][0], points[0][1] + 20)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
        time.sleep(1)
        self.find_chop_places()

    def find_chop_places(self):

        chop_places = vision.Vision(cv2.imread(resource_path("images/chop_places.png")))

        while True:

            img = self.NosTale_window.get_screenshot()

            self.chop_places_points = chop_places.find(img, threshold=0.95)

            if len(self.chop_places_points) == 2:
                break

        self.playing = True
        self.failed = False
        self.start_game()

    def start_game(self):

        wood = vision.Vision(cv2.imread(resource_path("images/wood.png")))
        result_window = vision.Vision(cv2.imread(resource_path("images/result_window.png")))

        self.score = Thread(target=self.checking_score_thread, args=())
        self.score.start()

        while self.playing:

            # IMG of the game
            try:
                img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            # Top chop place
            chop_place_1_y = self.chop_places_points[0][1] - 80
            chop_place_1_x = self.chop_places_points[0][0] - 20
            chop_place_1 = img[int(chop_place_1_y):int(chop_place_1_y + 90),
                           int(chop_place_1_x):int(chop_place_1_x + 45)].copy()

            # Bottom chop place
            chop_place_2_y = self.chop_places_points[1][1] - 80
            chop_place_2_x = self.chop_places_points[1][0] - 20
            chop_place_2 = img[int(chop_place_2_y):int(chop_place_2_y + 90),
                           int(chop_place_2_x):int(chop_place_2_x + 45)].copy()

            chop_place_1_points = wood.find(chop_place_1, threshold=0.95)
            chop_place_2_points = wood.find(chop_place_2, threshold=0.95)

            if chop_place_1_points:

                self.click(win32con.VK_LEFT)

            elif chop_place_2_points:

                self.click(win32con.VK_RIGHT)

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

            if result_window.find(result_window_crop_img, threshold=0.90):
                self.failed = True
                self.playing = False
                break

        if not self.playing:
            self.stop_game()

    def stop_game(self):
        get_reward = vision.Vision(cv2.imread(resource_path("images/get_reward.png")))

        if not self.failed:

            while True:

                try:
                    img = self.NosTale_window.get_screenshot()
                except Exception:
                    continue

                reward_points = get_reward.find(img, threshold=0.95)

                if reward_points:
                    break

                time.sleep(0.1)

            # Click Reward button
            lParam = win32api.MAKELONG(reward_points[0][0], reward_points[0][1] + 20)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(0.7)

            # Click level reward
            reward_button_y = int(img.shape[0] / 2 + 50)
            reward_button_x = int((img.shape[1] / 2 + (int(self.reward_level) - 3) * 70) if int(self.reward_level) >= 3 else (
                    img.shape[0] / 2 - (int(self.reward_level) - 3) * 70))

            lParam = win32api.MAKELONG(reward_button_x, reward_button_y)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_MOUSEMOVE, None, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_LBUTTONUP, None, lParam)
            time.sleep(0.6)

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
            time.sleep(1)

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

                self.if_sawmill_start_exists()

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

            self.if_sawmill_start_exists()
