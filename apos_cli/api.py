import requests
import datetime
from .misc import COLORS

class APOS_API:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.set_token(token)

        self.active_group_orders = []
        self.user_items = []
        self.user_groups = []

    def set_token(self, token):
        self.token = token

    def get_token(self):
        return self.token

    def test_auth_connection(self):

        test_url = self.config['base_url'] + "orders"

        resp = requests.get(test_url, headers=self._get_auth())

        if resp.status_code in [404, 500]:
            print(f"API error (http {resp.status_code})")

        if resp.status_code in [401, 403]:
            print(f"Authentification failed (http {resp.status_code})")

        if resp.status_code in [200,]:
            print(f"{COLORS.OKBLUE}Connected to API (http {resp.status_code}){COLORS.ENDC}")

    def login(self, username, password):
        resp = requests.post(self.base_url + "auth", \
            data={"username": username, "password": password})
        if resp.status_code == 200:
            self.set_token(resp.json()['token'])
            return True
        else:
            return False

    def _get_auth(self):
        if self.token is None:
            print(f"{COLORS.WARNING}Please login before any other command!{COLORS.ENDC}")
            exit(1)
        return {'Authorization': f"Bearer {self.get_token()}"}

    def pull_active_group_orders(self):
        resp = requests.get(self.base_url + "orders/active",
                            headers=self._get_auth())

        if resp.status_code == 200:
            self.active_group_orders = resp.json()
            return True
        else:
            return False

    def get_active_group_orders(self):
        return self.active_group_orders

    def create_group_order(self, title, description, deadline, location, deliverer):
        order = {}
        order['title'] = title
        order['description'] = description
        order['deadline'] = deadline
        order['location'] = location
        order['deliverer'] = deliverer

        resp = requests.put(self.base_url + "orders",
                        json=order,
                        headers=self._get_auth())
        if resp.status_code == 201:
            return True, resp.json()['id']
        else:
            return False, -1

    def create_item(self, order_id, name, tip_percent, price):
        item = {}
        item['name'] = name
        item['tip_percent'] = tip_percent
        item['price'] = price

        resp = requests.put(f"{self.base_url}orders/{order_id}/items",
                        json=item,
                        headers=self._get_auth())

        if resp.status_code == 201:
            return True
        else:
            return False

    def pull_user_items(self):
        resp = requests.get(self.base_url + "user/items",
                            headers=self._get_auth())

        if resp.status_code == 200:
            self.user_items = resp.json()
            return True
        else:
            return False

    def get_user_items(self):
        return self.user_items

    def pull_user_groups(self):
        resp = requests.get(self.base_url + "user/orders",
                            headers=self._get_auth())

        if resp.status_code == 200:
            self.user_items = resp.json()
            return True
        else:
            return False

    def get_user_groups(self):
        return self.user_items

    def set_order_arrived(self, order_id, arrival_time=None):
        if not arrival_time:
            arrival_time = datetime.datetime.now()

        arrival_time = arrival_time.timestamp()

        resp = requests.patch(f"{self.base_url}orders/{order_id}",
                            json={'arrival': arrival_time},
                            headers=self._get_auth())

        if resp.status_code == 200:
            return True
        else:
            return False

    def get_order_infos(self, order_id):
        resp = requests.get(f"{self.base_url}orders/{order_id}",
                            headers=self._get_auth())

        if resp.status_code == 200:
            return True, resp.json()
        else:
            return False, None

    def get_items_for_order(self, order_id):
        resp = requests.get(f"{self.base_url}orders/{order_id}/items",
                            headers=self._get_auth())

        if resp.status_code == 200:
            return True, resp.json()
        else:
            return False, None
