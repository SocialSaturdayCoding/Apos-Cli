#! /usr/bin/python3

import argparse
from datetime import datetime, timedelta
import yaml
import getpass
import os
import requests
from tabulate import tabulate


class COLORS:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_error(error):
    print(COLORS.FAIL + COLORS.BOLD + error + COLORS.ENDC)


parser = argparse.ArgumentParser(description=f"Command Line Interface for {COLORS.WARNING}'APOS - Agile Pizza Ordering Service'{COLORS.ENDC}")

subparsers = parser.add_subparsers(title="command", description="command which shall be performed", dest="command")

parser_add = subparsers.add_parser("order", help="Add, view or modify group orders")
parser_add.add_argument("-l", "--list", dest="list", action='store_true', help="Lists all active group orders")
parser_add.add_argument("-c", "--create", dest="create", action='store_true', help="Creates a group order")

parser_get = subparsers.add_parser("item", help="Add or modifies your items for a group order")

parser_login = subparsers.add_parser("login",
                                     help="login to your account and create a token for authentication, do this first!")

args = parser.parse_args()

base_url = "http://localhost:5000/api/v1/"

config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
config_path = os.path.join(config_dir, "apos")
config = {}

if args.command != "login":
    try:
        f = open(config_path, mode='r')
        config = yaml.load(f, Loader=yaml.Loader)
        f.close()
    except FileNotFoundError:
        print("Please login before any other command")
        exit(1)


def write_config():
    try:
        f = open(config_path, "w+")
        yaml.dump(config, f)
        f.close()
    except Exception as ex:
        print(ex)
        exit(1)

def login():
    user = input("Enter Username: ")
    password = getpass.unix_getpass("Enter Password: ")
    resp = requests.post(base_url + "auth", data={"username": user, "password": password})
    if resp.status_code == 200:
        config['token'] = resp.json()['token']
        write_config()
        print(f"{COLORS.BOLD}{COLORS.OKGREEN}Login Successful{COLORS.ENDC}")
    else:
        print_error("Login not successful:")
        print_error(f"Server returned {resp.status_code}")
        print(COLORS.FAIL + resp.text + COLORS.ENDC)
        exit(1)

def list_active_group_orders():
    resp = requests.get(base_url + "orders/active",
                        headers={'Authorization': f"Bearer {config['token']}"})
    if resp.status_code == 200:
        orders = resp.json()

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

        return orders, fromated_orders
    else:
        print_error("Request not successful:")
        print_error(f"Server returned {resp.status_code}")
        print(COLORS.FAIL + resp.text + COLORS.ENDC)
        exit(1)

def create_group_order():
    order = {}
    print("\nYou are creating a group order. Other people can add their items to your group order. Please check if there are \n")
    order['title'] = input("Whats the title of your order?  ")
    order['description'] = input("Enter a description:\n")
    order['deadline'] = (datetime.now() + timedelta(minutes=int(input("In how many minute do you order at the delivery service?  ")))).timestamp()
    order['location'] = input("Where are you?  ")
    order['deliverer'] = input("Whats the delivery service?  ")
    if input("\n\nCreate order? (y/n)  ") == "y":
        resp = requests.put(base_url + "orders",
                        json=order,
                        headers={'Authorization': f"Bearer {config['token']}"})
        if resp.status_code == 200:
            print("Order submitted " + COLORS.OKBLUE + "successfully!" + COLORS.ENDC)
        else:
            print_error("Order not successful:")
            print_error(f"Server returned {resp.status_code}")
            print(COLORS.FAIL + resp.text + COLORS.ENDC)
            exit(1)
    else:
        print("Abort")


if args.command == "login":
    login()

elif args.command == "order":
    if args.list:
        list_active_group_orders()
    if args.create:
        create_group_order()
