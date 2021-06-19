import time
import cv2
from threading import Thread

import win32api

import static_data
import vision
import WindowCapture
import check_score
from static_data import *
from ConsoleColors import Colors


class PondGame:
    def __init__(self, NosTale_name, repeats, level):
        self.NosTale_hwnd = win32gui.FindWindow('TNosTaleMainF', NosTale_name)
        self.NosTale_name = NosTale_name
        self.NosTale_window = WindowCapture.WindowCapture(window_hwnd=self.NosTale_hwnd)
        self.score_checker = check_score.CheckScore(
            cv2.imread(resource_path("images/score_digits.png"), cv2.IMREAD_GRAYSCALE))
        self.bat_pixel_rgb = [(33, 36, 170), (32, 35, 170), (39, 49, 210)]
        self.catch_rgb = [(255, 247, 198), ]
        self.combo_fish_rgb = [(1, 218, 255), ]
        self.playing = False
        self.failed = False
        self.reward_level = level
        self.repeats = repeats
        self.repeats_counter = 1
        self.score_levels = [0, 1000, 4000, 8000, 12000, 20000]
        self.resolution_index = get_resolution(self.NosTale_window)
        if self.resolution_index != -1:
            self.if_pond_start_exists()
        else:
            print(Colors.WARNING + "Unsupported resolution, sorry...")
            time.sleep(2)
            exit(1)

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

    # Checks if game window is opened
    def if_pond_start_exists(self):
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
                self.find_bobs()
                break
            time.sleep(1)

    # Defines images to variables and starts game
    def find_bobs(self):
        try:
            self.left_bot_bob = vision.Vision(cv2.imread(resource_path("images/bob_left_bot.png")))
            self.right_top_bob = vision.Vision(cv2.imread(resource_path("images/bob_top_right.png")))

            if self.left_bot_bob and self.right_top_bob:
                print(Colors.OKGREEN +
                      "[" + str(self.NosTale_name) + "] Doing " +
                      str(self.repeats_counter) + "/" +
                      str(self.repeats) +
                      " repeat")
                time.sleep(0.1)
                self.play_game()
        except:
            self.if_pond_start_exists()

    # Single click of key with delay
    def click(self, key, delay=True):
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, key, 0x002C0001)
        win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, key, 0xC02C0001)
        if delay:
            time.sleep(0.60)

    # Checks if bat is over bob
    def check_bat_over_bob(self, img, key):

        if not detect_color(self.bat_pixel_rgb, img):
            self.click(key)

    # Main functionality
    def play_game(self):
        img = self.NosTale_window.get_screenshot()

        while True:
            left_bob, bot_bob = self.left_bot_bob.find(img, threshold=0.95)
            top_bob, right_bob = self.right_top_bob.find(img, threshold=0.95)

            if left_bob and bot_bob and top_bob and right_bob:
                break

        self.score = Thread(target=self.checking_score_thread, args=())
        self.score.start()

        while self.playing:

            # IMG for checking if fish catches
            try:
                img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            left_bob_img = img[int(left_bob[1] - 19):int(left_bob[1] - 16),
                           int(left_bob[0] + 8):int(left_bob[0] + 14)].copy()
            bot_bob_img = img[int(bot_bob[1] - 19):int(bot_bob[1] - 16),
                          int(bot_bob[0] + 8):int(bot_bob[0] + 14)].copy()
            top_bob_img = img[int(top_bob[1] - 19):int(top_bob[1] - 16),
                          int(top_bob[0] + 8):int(top_bob[0] + 14)].copy()
            right_bob_img = img[int(right_bob[1] - 19):int(right_bob[1] - 16),
                            int(right_bob[0] + 8):int(right_bob[0] + 14)].copy()

            # IMG for combo fish
            combo_fish_crop_img = img[int(left_bob[1] - 16):int(left_bob[1] - 13),
                                  int(left_bob[0] - 30):int(left_bob[0] - 25)].copy()

            if detect_color(self.combo_fish_rgb, combo_fish_crop_img):

                self.solve_combo_fish()
                time.sleep(1)

            else:

                if detect_color(self.catch_rgb, left_bob_img):
                    self.check_bat_over_bob(left_bob_img, win32con.VK_LEFT)

                if detect_color(self.catch_rgb, bot_bob_img):
                    self.check_bat_over_bob(bot_bob_img, win32con.VK_DOWN)

                if detect_color(self.catch_rgb, top_bob_img):
                    self.check_bat_over_bob(top_bob_img, win32con.VK_UP)

                if detect_color(self.catch_rgb, right_bob_img):
                    self.check_bat_over_bob(right_bob_img, win32con.VK_RIGHT)

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

            time.sleep(0.05)

        time.sleep(0.1)

        if not self.playing:
            self.stop_game()

    # Check end
    def stop_game(self):
        self.score.join()

        if not self.failed:

            while not self.failed:

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
                    break

                self.click(win32con.VK_LEFT, False)

                time.sleep(0.5)

            time.sleep(0.7)

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

                print(Colors.WARNING + "[" + str(self.NosTale_name) + "] Not enough points to play" + Colors.OKGREEN)

                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0x002C0001)
                win32gui.SendMessage(self.NosTale_hwnd, win32con.WM_KEYUP, win32con.VK_ESCAPE, 0xC02C0001)

                chosen_options_x, chosen_options_y = static_data.get_stop_position(img)

                lParam = win32api.MAKELONG(chosen_options_x, chosen_options_y)
                click_at(lParam, self.NosTale_hwnd)
                time.sleep(1)

            elif self.repeats_counter <= self.repeats:

                self.if_pond_start_exists()

        else:
            time.sleep(0.1)

            img = self.NosTale_window.get_screenshot()
            chosen_options_x, chosen_options_y = static_data.get_play_again_after_fail_position(img)

            lParam = win32api.MAKELONG(chosen_options_x, chosen_options_y)
            click_at(lParam, self.NosTale_hwnd)
            time.sleep(1)

            print(Colors.FAIL + "[" + str(self.NosTale_name) + "] Bot failed and will try again" + Colors.OKGREEN)

            self.if_pond_start_exists()

    # Solving combo fish
    def solve_combo_fish(self):
        arrow_left = vision.Vision(cv2.imread(resource_path("images/arrow_left.jpg")))
        arrow_up = vision.Vision(cv2.imread(resource_path("images/arrow_up.jpg")))
        arrow_right = vision.Vision(cv2.imread(resource_path("images/arrow_right.jpg")))
        arrow_down = vision.Vision(cv2.imread(resource_path("images/arrow_down.jpg")))

        combo = 0

        start = time.time()

        while combo < 8 and time.time() - start <= 3.5:
            try:
                img = self.NosTale_window.get_screenshot()
            except Exception:
                continue

            x = img.shape[1] / 2
            y = img.shape[0] / 2
            crop_img = img[int(y - 10):int(y + 25), int(x - 160):int(x + 230)].copy()

            if arrow_left.find(crop_img, threshold=0.95):
                self.click(win32con.VK_LEFT, False)
                combo += 1

            elif arrow_up.find(crop_img, threshold=0.95):
                self.click(win32con.VK_UP, False)
                combo += 1

            elif arrow_right.find(crop_img, threshold=0.95):
                self.click(win32con.VK_RIGHT, False)
                combo += 1

            elif arrow_down.find(crop_img, threshold=0.95):
                self.click(win32con.VK_DOWN, False)
                combo += 1

            time.sleep(0.1)

        time.sleep(0.2)
