#! /usr/bin/python3

import argparse
from datetime import datetime, timedelta
import yaml
import getpass
import os
from tabulate import tabulate
from misc import COLORS, pizza
from api import APOS_API

class APOS:

    def __init__(self):
        print(f"Welcome to {COLORS.WARNING}APOS the Agile Pizza Ordering Service{COLORS.ENDC}\n{pizza}")

        parser = argparse.ArgumentParser(description=f"Command Line Interface for {COLORS.WARNING}'APOS - Agile Pizza Ordering Service'{COLORS.ENDC}")

        subparsers = parser.add_subparsers(title="command", description="command which shall be performed", dest="command")

        parser_order = subparsers.add_parser("order", help="Add, view or modify group orders")

        parser_show = subparsers.add_parser("show", help="Add, view or modify group orders")

        parser_login = subparsers.add_parser("login",
                                            help="login to your account and create a token for authentication, do this first!")

        args = parser.parse_args()

        self.default_base_url = "http://localhost:5000/api/v1/"

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

        if args.command == "show":
            self.start_show()

    def print_error(self, error):
        print(COLORS.FAIL + COLORS.BOLD + error + COLORS.ENDC)

    def load_config(self):
        if not os.path.isfile(self.config_path):
            self.config['base_url'] = self.default_base_url
            self.write_config()
            print(f"{COLORS.WARNING}Create new config!{COLORS.ENDC}")
        else:
            f = open(self.config_path, mode='r')
            self.config = yaml.load(f, Loader=yaml.Loader)
            f.close()

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
                    self.create_item(self.get_id_for_active_order(int(user_input)))
                    return
                else:
                    print(f"{COLORS.WARNING}Invalid group id!{COLORS.ENDC}")
                    self.start_order()
                    return
            elif user_input == "c":
                print("Creating a new group!")
                success, group_id = self.create_group_order()
                if success:
                    if input("Order some thing in the newly created group?\n ~ (y/n):") == "y":
                        self.create_item(group_id)
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
                success, group_id = self.create_group_order()
                if success:
                    if input("Order some thing in the newly created group?\n ~ (y/n):") == "y":
                        self.create_item(group_id)
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
                else:
                    order_formated['arrival'] = "Unknown"

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
        print("\nYou are creating a group order. Other people can add their items to your group order. Please check if there are \n")
        order = {}
        order['title'] = input("Whats the title of your order?  ")
        order['description'] = input("Enter a description:\n")
        order['deadline'] = (datetime.now() + timedelta(minutes=int(input("In how many minute do you order at the delivery service?  ")))).timestamp()
        order['location'] = input("Where are you?  ")
        order['deliverer'] = input("Whats the delivery service?  ")

        if input("\nCreate group? (y/n)  ") == "y":
            success, group_id = self.api.create_group_order(**order)
            if success:
                print("Group created " + COLORS.OKBLUE + "successfully!" + COLORS.ENDC)
                print("Use 'apos show groups' to browse the groups you are responsible for.")
                return True, group_id
            else:
                self.print_error("Order not successful:") # TODO better error msg
                exit(1)
        else:
            if input("\nRetry creating a group? (y/n)  ") == "y":
                return self.create_group_order()
            else:
                print("Abort")
                return False, group_id

    def create_item(self, group_id):
        print(f"\nYou are creating a new item for the selected group order. \n") # TODO query group order for name
        item = {}
        item['name'] = input("What do you want to order? Enter pizza type and all extra whishes:\n")
        item['tip_percent'] = input("Enter the amount of tip you want to spent (in percent):")
        item['price'] = input("Whats the price of your pizza. \nStay fair and enter the real pice. \nThis makes things much easier for the group creator! Enter price in Euro:")


        if input("\nCreate item? (y/n)") == "y":
            if self.api.create_item(group_id, **item):
                print("Item added " + COLORS.OKBLUE + "successfully!" + COLORS.ENDC)
                print("Use 'apos show orders' to view your personal orders and see their current state.")
                return True
            else:
                self.print_error("Order not successful!") # TODO better error msg

        if input("\nRetry creating the item? (y/n)  ") == "y":
            return self.create_item(group_id)
        else:
            print("Abort")
            return False

    def get_id_for_active_order(self, active_order_id):
        return self.api.get_active_group_orders()[active_order_id]['id']

    def start_show(self):
        past = 2

        print(f"This command is used to show recently (past {past} days) created groups or items.")

        goal = input("\n1) Show ordered pizzas\n2) Show created groups\n\nEnter numer: (1|2) ")

        if goal == "1":
            self.show_user_items(past=past)
        elif goal == "2":
            self.show_user_groups(past=past)
        else:
            print("What are you doing? I asked for 1 or 2!")

    def show_user_groups(self, past=2):
        if self.api.pull_user_groups():
            orders = self.api.get_user_groups()

            #Format
            fromated_orders = []
            for order in orders:
                if (datetime.now() - datetime.fromtimestamp(int(order['deadline']))).days < past:
                    order_formated = {
                        'title': order['title'],
                        'description': order['description'],
                        'location': order['location'],
                        'deliverer': order['deliverer'],
                        'deadline': datetime.fromtimestamp(int(order['deadline']))
                        }

                    if 'arrival' in order.keys():
                        order_formated['arrival'] = datetime.fromtimestamp(int(order['arrival']))
                    else:
                        order_formated['arrival'] = "Unknown"

                    fromated_orders.append(order_formated)

            header_bar = {
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

    def show_user_items(self, past=2):
        if self.api.pull_user_items():
            items = self.api.get_user_items()

            #Format
            fromated_items = []
            for item in items:
                order = item['order']
                if (datetime.now() - datetime.fromtimestamp(int(order['deadline']))).days < past:
                    item_formated = {
                        'name': item['name'],
                        'tip': item['tip_percent'],
                        'price': item['price'],
                        'deadline': datetime.fromtimestamp(int(order['deadline'])),
                        }

                    if 'arrival' in order.keys():
                        item_formated['arrival'] = datetime.fromtimestamp(int(order['arrival']))
                    else:
                        item_formated['arrival'] = "Unknown"

                    fromated_items.append(item_formated)

            header_bar = {
                'name': "Name",
                'tip': 'Tip',
                'price': "Price",
                'deadline': "Deadline",
                'arrival': "Arrival",
                }

            # Show result
            print(tabulate(fromated_items, headers=header_bar, tablefmt="simple", showindex="always"))
        else:
            self.print_error("Request not successful:")
            exit(1)


if __name__ == "__main__":
    APOS()
