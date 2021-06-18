import time
import cv2
from threading import Thread

import win32api

import check_score
import static_data
import vision
import WindowCapture
from ConsoleColors import Colors
from static_data import *


class Sawmill:
    def __init__(self, NosTale_name, repeats, level):
        self.NosTale_hwnd = win32gui.FindWindow('TNosTaleMainF', NosTale_name)
        self.NosTale_name = NosTale_name
        self.NosTale_window = WindowCapture.WindowCapture(window_hwnd=self.NosTale_hwnd)
        self.score_checker = check_score.CheckScore(
            cv2.imread(resource_path("images/score_digits.png"), cv2.IMREAD_GRAYSCALE))
        self.repeats = repeats
        self.repeats_counter = 1
        self.reward_level = level
        self.score_levels = [0, 1010, 5010, 10010, 14010, 18010]
        self.playing = False
        self.failed = False
        self.wood_rgb = [(17, 49, 69), ]
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

            time.sleep(1)

    def if_sawmill_start_exists(self):
        start = time.time()
        while time.time() - start < 5:
            print(Colors.OKCYAN + "[" + str(self.NosTale_name) + "] Searching for start button...")
            img = self.NosTale_window.get_screenshot()
            x, y = static_data.get_start_game_position(img)
            img = self.NosTale_window.get_screenshot()[(y - 1):(y + 1), (x - 1):(x + 1)]
            if static_data.detect_color(StaticData.start_game_rgb, img):
                print(Colors.OKGREEN + "[" + str(self.NosTale_name) + "] Found start button!")
                lParam = win32api.MAKELONG(x, y)
                click_at(lParam, self.NosTale_hwnd)
                time.sleep(1)
                self.playing = True
                self.failed = False
                self.find_chop_places()
                break
            time.sleep(1)

    def click(self, key):
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, key, 0x002C0001)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, key, 0xC02C0001)

    def find_chop_places(self):

        try:
            chop_places = vision.Vision(cv2.imread(resource_path("images/chop_places.png")))

            while True:

                img = self.NosTale_window.get_screenshot()

                chop_top, chop_bot = chop_places.find(img, threshold=0.95)

                if chop_top and chop_bot:
                    self.chop_places_points = chop_top, chop_bot
                    break

            self.playing = True
            self.failed = False
            self.start_game()
        except:
            self.if_sawmill_start_exists()

    def start_game(self):
        self.score = Thread(target=self.checking_score_thread, args=())
        self.score.start()

        while self.playing:

            # IMG of the game
            try:
                img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            # Top chop place
            chop_place_1_y = self.chop_places_points[0][1] - 60
            chop_place_1_x = self.chop_places_points[0][0] - 5
            chop_place_1 = img[int(chop_place_1_y):int(chop_place_1_y + 60),
                           int(chop_place_1_x):int(chop_place_1_x + 10)].copy()

            # Bottom chop place
            chop_place_2_y = self.chop_places_points[1][1] - 60
            chop_place_2_x = self.chop_places_points[1][0] - 5
            chop_place_2 = img[int(chop_place_2_y):int(chop_place_2_y + 60),
                           int(chop_place_2_x):int(chop_place_2_x + 10)].copy()

            if detect_color(self.wood_rgb, chop_place_1):

                self.click(win32con.VK_LEFT)
                time.sleep(0.3)

            elif detect_color(self.wood_rgb, chop_place_2):

                self.click(win32con.VK_RIGHT)
                time.sleep(0.3)

            # Full IMG
            try:
                fail_img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            # IMG for result window
            result_window_x = fail_img.shape[1] / 2 - 5
            result_window_y = fail_img.shape[0] / 2 - 60
            result_window_crop_img = fail_img[int(result_window_y):int(result_window_y + 10),
                                     int(result_window_x):int(result_window_x + 10)].copy()

            if detect_color(StaticData.result_window_rgb, result_window_crop_img):
                self.failed = True
                self.playing = False
                break

        if not self.playing:
            self.stop_game()

    def stop_game(self):

        if not self.failed:

            while True:

                try:
                    img = self.NosTale_window.get_screenshot()
                except Exception:
                    continue

                # IMG for result window
                result_window_x = img.shape[1] / 2 - 5
                result_window_y = img.shape[0] / 2 - 60
                result_window_crop_img = img[int(result_window_y):int(result_window_y + 10),
                                         int(result_window_x):int(result_window_x + 10)].copy()

                if detect_color(StaticData.result_window_rgb, result_window_crop_img):
                    break

                time.sleep(1)

            # Click Reward button
            img = self.NosTale_window.get_screenshot()
            x, y = static_data.get_reward_position(img)
            lParam = win32api.MAKELONG(x, y)
            click_at(lParam, self.NosTale_hwnd)
            time.sleep(0.7)

            # Click level reward
            img = self.NosTale_window.get_screenshot()
            x, y = static_data.get_level_reward_position(img, self.reward_level)
            lParam = win32api.MAKELONG(x, y)
            click_at(lParam, self.NosTale_hwnd)
            time.sleep(0.7)

            self.repeats_counter += 1

            img = self.NosTale_window.get_screenshot()

            if self.repeats_counter <= self.repeats:

                chosen_options_x, chosen_options_y = static_data.get_play_again_position(img)

            else:

                chosen_options_x, chosen_options_y = static_data.get_stop_position(img)
                print(Colors.UNDERLINE +
                      Colors.OKBLUE +
                      "[" + str(self.NosTale_name) + "] Has finished all repeats" +
                      Colors.OKGREEN)

            lParam = win32api.MAKELONG(chosen_options_x, chosen_options_y)
            click_at(lParam, self.NosTale_hwnd)
            time.sleep(0.7)

            end_img = self.NosTale_window.get_screenshot()

            # IMG for result window
            result_window_x = end_img.shape[1] / 2 - 400 / 2
            result_window_y = end_img.shape[0] / 2 - 200 / 2
            result_window_crop_img = end_img[int(result_window_y):int(result_window_y + 200),
                                     int(result_window_x):int(result_window_x + 400)].copy()

            if vision.Vision(cv2.imread(resource_path("images/not_enough_points.png"))).find(result_window_crop_img,
                                                                                             threshold=0.9):

                exit(0)

                print(Colors.WARNING + "[" + str(self.NosTale_name) + "] Not enough points to play" + Colors.OKGREEN)

                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0x002C0001)
                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0xC02C0001)

                chosen_options_x, chosen_options_y = static_data.get_stop_position(img)

                lParam = win32api.MAKELONG(chosen_options_x, chosen_options_y)
                click_at(lParam, self.NosTale_hwnd)
                time.sleep(1)

            elif self.repeats_counter <= self.repeats:

                self.if_sawmill_start_exists()

        else:
            time.sleep(0.1)

            img = self.NosTale_window.get_screenshot()
            chosen_options_x, chosen_options_y = static_data.get_play_again_after_fail_position(img)

            lParam = win32api.MAKELONG(chosen_options_x, chosen_options_y)
            click_at(lParam, self.NosTale_hwnd)
            time.sleep(1)

            print(Colors.FAIL + "[" + str(self.NosTale_name) + "] Bot failed and will try again" + Colors.OKGREEN)

            self.if_sawmill_start_exists()
