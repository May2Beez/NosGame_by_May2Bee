import os
import time

import pond_game
import sawmill_game
from ConsoleColors import *


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

def choose_level(option, repeats):
    window_name = 'Nostale'
    os.system('cls')
    print("Which level reward do you want?")
    level = input("Level: ")

    if int(level) in range(1, 6):

        os.system('cls')
        print("BOT LOGS")

        if option in ('1', '2'):
            print(Colors.OKGREEN + "[" + str(window_name) + "] Started bot at " + str(
                time.strftime("%H:%M:%S", time.localtime())) + " - " +
                  str(repeats) + " times - " + str(level) + " level")

            if option == '1':

                pond_game.PondGame(window_name, int(repeats), level)

            elif option == '2':

                sawmill_game.Sawmill(window_name, int(repeats), level)

            elif option == '3':

                pass

            elif option == '4':

                pass

            print(Colors.OKBLUE + "[" + str(window_name) + "] Finished at " + str(
                time.strftime("%H:%M:%S", time.localtime())) + " - " +
                  str(repeats) + " times - " + str(level) + " level" + Colors.ENDC)

    else:
        choose_level(option, repeats)


# Choosing repeats number

def repeats_number(option):
    os.system('cls')
    print("How many times do you want to repeat?")
    number = input("Repeats: ")

    if number.isnumeric():

        choose_level(option, number)

    else:
        print("Put only integer value from 1-20")


# Choosing minigame

def choose_option():
    option = input(Colors.HEADER + "Your option: ")

    if option == '1':
        repeats_number(option)
    elif option == '2':
        repeats_number(option)
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


if __name__ == "__main__":

    gui()
    option = choose_option()

    while option != '0':
        gui()
        option = choose_option()
