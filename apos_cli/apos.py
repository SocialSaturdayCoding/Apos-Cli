#! /usr/bin/python3

import os
import yaml
import getpass
import argparse
from datetime import datetime, timedelta
from tabulate import tabulate
from .misc import COLORS, pizza, int_eurocent_to_float_euro_string, parse_input, print_error
from .api import APOS_API, AuthException, NoTokenException, ConnectionException, GeneralAPIException

class APOS:

    def __init__(self):
        print(f"\nWelcome to {COLORS.WARNING}APOS the Agile Pizza Ordering Service{COLORS.ENDC}\n{pizza}")

        parser = argparse.ArgumentParser(description=f"Command Line Interface for {COLORS.WARNING}'APOS - Agile Pizza Ordering Service'{COLORS.ENDC}")

        subparsers = parser.add_subparsers(title="command", description="command which shall be performed", dest="command")

        parser_order = subparsers.add_parser("order", help="Add your order to a group order")

        parser_show = subparsers.add_parser("show", help="Show the items you ordered or the groups you created")

        parser_arrived = subparsers.add_parser("arrived", help="Flag a order as arrived")

        parser_info = subparsers.add_parser("info", help="Get all infos to order at the delivery service")

        parser_login = subparsers.add_parser("login",
                                            help="Login to your account and create a token for authentication, do this first!")

        args = parser.parse_args()

        self.default_base_url = "http://localhost:5000/api/v1/"

        config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        self.config_path = os.path.join(config_dir, "apos")
        self.config = {}

        self.load_config()

        self.api = APOS_API(self.config["base_url"], self.config.get("token", None))

        try:
            self.decisions(args)
        except AuthException as ae:
            print(f"{COLORS.WARNING}Invalid authentification!{COLORS.ENDC}")
            exit(0)
        except NoTokenException as nte:
            print(f"{COLORS.WARNING}Please login before any other command!{COLORS.ENDC}")
            exit(0)
        except ConnectionException as ce:
            print(f"{COLORS.WARNING}Failed to contact the backend!{COLORS.ENDC}")
            exit(0)


    def decisions(self, args):
        if args.command == "login":
            self.login()

        self.api.test_auth_connection()

        if args.command == "order":
            self.start_order()

        if args.command == "show":
            self.start_show()

        if args.command == "arrived":
            self.start_arrived()

        if args.command == "info":
            self.start_info()

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
            print_error(ex)
            exit(1)

    def login(self):
        user = input("Enter Username: ")
        password = getpass.unix_getpass("Enter Password: ")

        try:
            self.api.login(user, password)
        except AuthException as ae:
            print_error("Login not successful:")
            if input("Try again? (y/n)") == "y":
                return self.login()
            else:
                print("Exit cli")
                exit(1)
        except GeneralAPIException as gae:
            print_error(f"General API error!\n{gae.message}")
            exit(1)

        self.config['token'] = self.api.get_token()
        self.write_config()
        print(f"{COLORS.BOLD}{COLORS.OKBLUE}Login Successful{COLORS.ENDC}")

    def start_order(self):
        print("Oh I see you are hungry. The purpose of APOS is to order Pizza together.\n")
        self.show_active_group_orders()
        num_groups = len(self.api.get_active_group_orders())
        if num_groups > 0:
            print(  """\nLook if there is a group you want to join with your order. \nEnter the the number of the group you want to join.\n"""
                    """Not satisfied with the the listed groups? Type c to create a new one or enter q to quit!""")
            user_input = input(f"~ (0-{num_groups - 1} | c | q) : ")

            if user_input.isdigit():
                if 0 <= int(user_input) < num_groups:
                    self.create_item(self.get_id_for_active_order(int(user_input)))
                    return
                else:
                    print(f"{COLORS.WARNING}Invalid group id!{COLORS.ENDC}")
                    self.start_order()
                    return
            elif user_input == "c":
                print("Creating a new group!")
                group_id = self.create_group_order()
                if input("Order some thing in the newly created group?\n ~ (y/n):") == "y":
                    self.create_item(group_id)
                return
            elif user_input == "q":
                print("Exit APOS")
                exit(0)
            else:
                print_error("Invalid input. Try again!")
                return self.start_order()
        else:
            print("\nThere are currently no active groups you can join. Feel free to create a new group and let others join your group.\n")
            if input("Create group?\n ~ (y/n):") == "y":
                print("Creating a new group!")
                group_id = self.create_group_order()
                if input("Order some thing in the newly created group?\n ~ (y/n):") == "y":
                    self.create_item(group_id)
                return
            else:
                print("Exit APOS")
                exit(0)

    def start_info(self):
        print("Get all infos for your group orders! \n")

        id_list = self.show_user_groups(show_arrival=True)

        if len(id_list) > 1:
            while True:
                user_input = input(f"Enter the group to get more information: (0-{len(id_list) - 1}) ")
                if user_input.isdigit() and 0 <= int(user_input) < len(id_list):
                    order_id = id_list[int(user_input)]
                    self.group_ordered_items_summary(order_id)
                    return
                else:
                    print_error("Invalid user input!")
        elif len(id_list) == 0:
            print("Only one group order avalabile.\n")
            self.group_ordered_items_summary(id_list[0])
        else:
            print("No group order avalabile.\n")


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

    def start_arrived(self):
        print("Mark a pizza group order as arrived! \n")

        _, id_list = self.show_user_groups(not_arrived=True, show_arrival=False)

        while True:
            user_input = input(f"Enter the group order which arrived: (0-{len(id_list) - 1}) ")

            if user_input.isdigit() and 0 <= int(user_input) < len(id_list):
                order_id = id_list[int(user_input)]
                self.api.set_order_arrived(order_id)
                exit(0)
            else:
                print(f"{COLORS.FAIL}Invalid user input!{COLORS.ENDC}")

    def create_group_order(self):
        print("\nYou are creating a group order. Other people can add their items to your group order. Please check if there are \n")
        order = {}
        order['title'] = input("Whats the title of your group?  ")
        order['description'] = input("Enter a description:\n")
        order['deadline'] = (datetime.now() + timedelta(minutes=int(parse_input("In how many minute do you order at the delivery service?  ", r"^\d+$")))).timestamp()
        order['location'] = input("Where are you?  ")
        order['deliverer'] = input("Whats the delivery service?  ")

        if input("\nCreate group? (y/n)  ") == "y":
            success, group_id = self.api.create_group_order(**order)
            if success:
                print("Group created " + COLORS.OKBLUE + "successfully!" + COLORS.ENDC)
                print("Use 'apos show groups' to browse the groups you are responsible for.")
                return True, group_id
            else:
                print_error("Order not successful") # TODO better error msg
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
        item['tip_percent'] = parse_input("Enter the amount of tip you want to spent (in %): ", r"^((100)|(\d{0,2}))$")
        item['price'] = parse_input("Whats the price of your pizza. \nStay fair and enter the real pice. \nThis makes things much easier for the group creator! Enter price in €:",
            r"^[+]?[0-9]*\.?[0-9]?[0-9]$", to_float=True) * 100

        if input("\nCreate item? (y/n)") == "y":
            if self.api.create_item(group_id, **item):
                print("Item added " + COLORS.OKBLUE + "successfully!" + COLORS.ENDC)
                print("Use 'apos show orders' to view your personal orders and see their current state.")
                return True
            else:
                print_error("Order not successful!") # TODO better error msg

        if input("\nRetry creating the item? (y/n)  ") == "y":
            return self.create_item(group_id)
        else:
            print("Abort")
            return False

    def get_id_for_active_order(self, active_order_id):
        return self.api.get_active_group_orders()[active_order_id]['id']

    def show_user_groups(self, past=2, not_arrived=False, show_arrival=True):
        self.api.pull_user_groups()

        orders = self.api.get_user_groups()

        id_list = []

        #Format
        fromated_orders = []
        for order in orders:
            if (datetime.now() - datetime.fromtimestamp(int(order['deadline']))).days < past:
                if not 'arrival' in order.keys() or not not_arrived:
                    order_formated = {
                        'title': order['title'],
                        'description': order['description'],
                        'location': order['location'],
                        'deliverer': order['deliverer'],
                        'deadline': datetime.fromtimestamp(int(order['deadline']))
                        }
                    if show_arrival:
                        if 'arrival' in order.keys():
                            order_formated['arrival'] = datetime.fromtimestamp(int(order['arrival']))
                        else:
                            order_formated['arrival'] = "Unknown"

                    fromated_orders.append(order_formated)
                    id_list.append(order['id'])

        header_bar = {
            'title': "Title",
            'location': 'Location',
            'deadline': "Deadline",
            'description': "Description",
            'deliverer': "Deliverer",
            'arrival': "Arrival"}

        # Show result
        print(tabulate(fromated_orders, headers=header_bar, tablefmt="simple", showindex="always"))

        return id_list

    def show_user_items(self, past=2):
        self.api.pull_user_items()

        items = self.api.get_user_items()

        #Format
        fromated_items = []
        for item in items:
            order = item['order']
            if (datetime.now() - datetime.fromtimestamp(int(order['deadline']))).days < past:
                item_formated = {
                    'name': item['name'],
                    'tip': int_eurocent_to_float_euro_string(item['tip_percent']),
                    'price': int_eurocent_to_float_euro_string(item['price']),
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

    def show_active_group_orders(self, pull=True, arrival=False):
        if pull:
            self.api.pull_active_group_orders()

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

            if arrival:
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

    def group_ordered_items_summary(self, group_id):
        items = self.api.get_items_for_order(group_id)

        if len(items) == 0:
            print(f"\n{COLORS.WARNING}There are no orders item registered for the order!\n{COLORS.ENDC}")
        else:
            #Format
            fromated_items = []

            price = 0
            tip = 0

            for item in items:
                item_formated = {
                    'name': item['name'],
                    'tip': int_eurocent_to_float_euro_string(item['tip_percent']),
                    'price': int_eurocent_to_float_euro_string(item['price']),
                    }

                tip += item['tip_percent']
                price += item['price']

                fromated_items.append(item_formated)

            header_bar = {
                'name': "Name",
                'tip': 'Tip',
                'price': "Price",
                }

            # Show result
            print(f"\n{COLORS.HEADER}{COLORS.BOLD}SUMMARY\n{COLORS.ENDC}")
            print(tabulate(fromated_items, headers=header_bar, tablefmt="simple", showindex="always"))

            print(f"{'-'*35}\n{COLORS.OKBLUE}{COLORS.BOLD}Total without tip: {int_eurocent_to_float_euro_string(price)}")
            print(f"Total tip: {int_eurocent_to_float_euro_string(tip)}\n{COLORS.ENDC}")


def run():
    APOS()

if __name__ == "__main__":
    run()
