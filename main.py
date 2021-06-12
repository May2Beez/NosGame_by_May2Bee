import ctypes
import os
import time

import psutil as psutil
import win32api
import win32con
import win32gui
import win32process

import pond_game
import sawmill_game
from ConsoleColors import *


NOSTALE_WINDOWS = {}


# Simple GUI
def gui():
    os.system('cls')
    print(Colors.BOLD + Colors.HEADER + "Welcome to NosGame, minigames bot made by May2Bee!")
    print(Colors.OKCYAN + "Choose your minigame by typing the number" + Colors.ENDC)
    print(Colors.OKCYAN + "1. Fishpond")
    print("2. Sawmill" + Colors.ENDC)
    print(Colors.FAIL + "3. Quarry (Not yet)")
    print("4. Firing Range (That will be hard)" + Colors.ENDC)
    print(Colors.BOLD + "0. Exit" + Colors.ENDC)


# Choosing level to play

def choose_level(option, repeats, window_title):
    os.system('cls')
    print("Which level reward do you want?")
    level = input("Level: ")

    if int(level) in range(1, 6):

        os.system('cls')
        print("BOT LOGS")

        if option in ('1', '2'):
            print(Colors.OKGREEN + "[" + str(window_title) + "] Started bot at " + str(
                time.strftime("%H:%M:%S", time.localtime())) + " - " +
                  str(repeats) + " times - " + str(level) + " level")

            if option == '1':

                pond_game.PondGame(window_title, int(repeats), level)

            elif option == '2':

                sawmill_game.Sawmill(window_title, int(repeats), level)

            elif option == '3':

                pass

            elif option == '4':

                pass

            print(Colors.OKBLUE + "[" + str(window_title) + "] Finished at " + str(
                time.strftime("%H:%M:%S", time.localtime())) + " - " +
                  str(repeats) + " times - " + str(level) + " level" + Colors.ENDC)

    else:
        choose_level(option, repeats)


# Choosing repeats number

def repeats_number(option, window_title):
    os.system('cls')
    print("How many times do you want to repeat?")
    number = input("Repeats: ")

    if number.isnumeric():

        choose_level(option, number, window_title)

    else:
        print("Put only integer value from 1-20")


# Choosing minigame

def choose_option(window_title):
    option = input(Colors.HEADER + "Your option: ")

    if option == '1':
        repeats_number(option, window_title)
    elif option == '2':
        repeats_number(option, window_title)
    elif option == '3':
        os.system('cls')
        print("Not yet supported")
        time.sleep(2)
        gui()
    elif option == '4':
        os.system('cls')
        print("Not yet supported")
        time.sleep(2)
        gui()
    elif option == '0':
        exit(0)
    else:
        os.system('cls')
        print("Option out of bounds")
        time.sleep(2)
        gui()

    return option


def choose_window():

    if len(NOSTALE_WINDOWS) > 0:

        print(Colors.HEADER + Colors.BOLD + "Choose NosTale client:" + Colors.ENDC + Colors.OKGREEN)

        for index, key in enumerate(NOSTALE_WINDOWS):
            print(str(index + 1) + ". " + str(NOSTALE_WINDOWS[key]))

        window_name = input(Colors.BOLD + "Your choose: ")

        return list(NOSTALE_WINDOWS.items())[(int(window_name)-1)][1]

    else:
        print(Colors.WARNING + "Bot couldn't find any NosTale clients! Terminating program")
        time.sleep(5)
        exit(0)


def rename_windows():
    global NOSTALE_WINDOWS

    def f(hwnd, more):
        title = win32gui.GetWindowText(hwnd)
        nostale_title = 'NosTale'
        if nostale_title in title:
            new_title = f"NosTale - ({hwnd})"
            NOSTALE_WINDOWS[hwnd] = new_title
            win32gui.SetWindowText(hwnd, new_title)

    win32gui.EnumWindows(f, None)


if __name__ == "__main__":

    rename_windows()
    window_title = choose_window()
    gui()
    option = choose_option(window_title)

    while option != '0':
        gui()
        option = choose_option(window_title)
