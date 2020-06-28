#! /usr/bin/python3

import argparse
from datetime import datetime, timedelta
import yaml
import getpass
import os
from tabulate import tabulate
from misc import COLORS
from api import APOS_API

class APOS:

    def __init__(self):
        print(f"Welcome to {COLORS.WARNING}APOS the Agile Pizza Ordering Service{COLORS.ENDC}\n")

        parser = argparse.ArgumentParser(description=f"Command Line Interface for {COLORS.WARNING}'APOS - Agile Pizza Ordering Service'{COLORS.ENDC}")

        subparsers = parser.add_subparsers(title="command", description="command which shall be performed", dest="command")

        parser_add = subparsers.add_parser("order", help="Add, view or modify group orders")
        parser_add.add_argument("-l", "--list", dest="list", action='store_true', help="Lists all active group orders")
        parser_add.add_argument("-c", "--create", dest="create", action='store_true', help="Creates a group order")

        parser_login = subparsers.add_parser("login",
                                            help="login to your account and create a token for authentication, do this first!")

        args = parser.parse_args()

        config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        self.config_path = os.path.join(config_dir, "apos")
        self.config = {}

        self.load_config()

        self.api = APOS_API(self.config["base_url"], self.config.get("token", None))

        if args.command == "login":
            self.login()
            exit(0)

        if args.command == "order":
            self.start_order()

    def print_error(self, error):
        print(COLORS.FAIL + COLORS.BOLD + error + COLORS.ENDC)

    def load_config(self):
        try:
            f = open(self.config_path, mode='r')
            self.config = yaml.load(f, Loader=yaml.Loader)
            f.close()
        except FileNotFoundError:
            self.print_error("Config file not found!") # TODO config creation wizard
            exit(1)

    def write_config(self):
        try:
            f = open(self.config_path, "w+")
            yaml.dump(self.config, f)
            f.close()
        except Exception as ex:
            self.print_error(ex)
            exit(1)

    def login(self):
        user = input("Enter Username: ")
        password = getpass.unix_getpass("Enter Password: ")

        if self.api.login(user, password):
            self.config['token'] = self.api.get_token()
            self.write_config()
            print(f"{COLORS.BOLD}{COLORS.OKGREEN}Login Successful{COLORS.ENDC}")
        else:
            self.print_error("Login not successful:")

            if input("Try again? (y/n)") == "y":
                self.login()
            else:
                print("Exit cli")
                exit(1)

    def start_order(self):
        print("Oh I see you are hungry. The purpose of APOS is to order Pizza together.\n")
        self.show_active_group_orders()
        num_groups = len(self.api.get_active_group_orders())
        if num_groups > 0:
            print(  """\nLook if there is a group you want to join with your order. \nEnter the the number of the group you want to join.\n"""
                    """Not satisfied with the the listed groups? Type c to create a new one or enter q to quit!""")
            user_input = input(f"~ (0-{num_groups - 1} | c | q) : ")

            if user_input.isdigit():
                if int(user_input) < num_groups:
                    print("TODO DO stuff")
                    return
                else:
                    print(f"{COLORS.WARNING}Invalid group id!{COLORS.ENDC}")
                    self.start_order()
                    return
            elif user_input == "c":
                print("Creating a new group!")
                self.create_group_order()
                return
            elif user_input == "q":
                print("Exit APOS")
                exit(0)
            else:
                self.print_error("Invalid input. Try again!")
                self.start_order()
                return
        else:
            print("\nThere are currently no active groups you can join. Feel free to create a new group and let others join your group.\n")
            if input("Create group?\n ~ (y/n):") == "y":
                print("Creating a new group!")
                self.create_group_order()
                return
            else:
                print("Exit APOS")
                exit(0)

    def show_active_group_orders(self, pull=True):
        success = self.api.pull_active_group_orders()

        success = success or not pull

        if success:
            orders = self.api.get_active_group_orders()

            #Format
            fromated_orders = []
            for order in orders:
                order_formated = {
                    'title': order['title'],
                    'description': order['description'],
                    'location': order['location'],
                    'deliverer': order['deliverer'],
                    'owner': order['owner']['username'],
                    'deadline': datetime.fromtimestamp(int(order['deadline']))
                    }

                if 'arrival' in order.keys():
                    order_formated['arrival'] = datetime.fromtimestamp(int(order['arrival']))

                fromated_orders.append(order_formated)

            header_bar = {
                'owner': "Creator",
                'title': "Title",
                'location': 'Location',
                'deadline': "Deadline",
                'description': "Description",
                'deliverer': "Deliverer",
                'arrival': "Arrival"}

            # Show result
            print(tabulate(fromated_orders, headers=header_bar, tablefmt="simple", showindex="always"))
        else:
            self.print_error("Request not successful:")
            exit(1)

    def create_group_order(self):
        order = {}
        print("\nYou are creating a group order. Other people can add their items to your group order. Please check if there are \n")
        order['title'] = input("Whats the title of your order?  ")
        order['description'] = input("Enter a description:\n")
        order['deadline'] = (datetime.now() + timedelta(minutes=int(input("In how many minute do you order at the delivery service?  ")))).timestamp()
        order['location'] = input("Where are you?  ")
        order['deliverer'] = input("Whats the delivery service?  ")

        if input("\nCreate group? (y/n)  ") == "y":
            if self.api.create_group_order(**order):
                print("Order submitted " + COLORS.OKBLUE + "successfully!" + COLORS.ENDC)
                return
            else:
                self.print_error("Order not successful:") # TODO better error msg
                exit(1)
        else:
            print("Abort")
            return



if __name__ == "__main__":
    APOS()
