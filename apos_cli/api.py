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

        test_url = self.base_url + "orders"

        try:
            resp = requests.get(test_url, headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(200, resp, auth=True)


    def login(self, username, password):
        try:
            resp = requests.post(self.base_url + "auth", \
                data={"username": username, "password": password})
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(200, resp, auth=True)

        self.set_token(resp.json()['token'])

    def _get_auth(self):
        if self.token is None:
            raise NoTokenException(message=f"Please login before any other command!")
        return {'Authorization': f"Bearer {self.get_token()}"}

    def pull_active_group_orders(self):
        try:
            resp = requests.get(self.base_url + "orders/active",
                            headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(200, resp, auth=True)

        self.active_group_orders = resp.json()

    def get_active_group_orders(self):
        return self.active_group_orders

    def create_group_order(self, title, description, deadline, location, deliverer):
        order = {}
        order['title'] = title
        order['description'] = description
        order['deadline'] = deadline
        order['location'] = location
        order['deliverer'] = deliverer

        try:
            resp = requests.put(self.base_url + "orders",
                        json=order,
                        headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(201, resp, auth=True)

        return resp.json()['id']

    def create_item(self, order_id, name, tip_percent, price):
        item = {}
        item['name'] = name
        item['tip_percent'] = tip_percent
        item['price'] = price

        try:
            resp = requests.put(f"{self.base_url}orders/{order_id}/items",
                        json=item,
                        headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(201, resp, auth=True)

        return resp.json()['id']

    def pull_user_items(self):
        try:
            resp = requests.get(self.base_url + "user/items",
                            headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(200, resp, auth=True)

        self.user_items = resp.json()

    def get_user_items(self):
        return self.user_items

    def pull_user_groups(self):
        try:
            resp = requests.get(self.base_url + "user/orders",
                            headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(200, resp, auth=True)

        self.user_groups = resp.json()

    def get_user_groups(self):
        return self.user_groups

    def set_order_arrived(self, order_id, arrival_time=None):

        if not arrival_time:
            arrival_time = datetime.datetime.now()

        arrival_time = arrival_time.timestamp()

        try:
            resp = requests.patch(f"{self.base_url}orders/{order_id}",
                            json={'arrival': arrival_time},
                            headers=self._get_auth())
        except requests.exceptions.ConnectionError as e:
            raise ConnectionException(previous=e, message="Failed to connect to API")

        self._check_response(200, resp, auth=True)

        self.user_groups = resp.json()

    def get_order_infos(self, order_id):
        resp = requests.get(f"{self.base_url}orders/{order_id}",
                            headers=self._get_auth())

        self._check_response(200, resp, auth=True)

        return resp.json()

    def get_items_for_order(self, order_id):
        resp = requests.get(f"{self.base_url}orders/{order_id}/items",
                            headers=self._get_auth())

        self._check_response(200, resp, auth=True)

        return resp.json()

    def _check_response(self, expected_http_code, response, auth=False):
        if response.status_code == expected_http_code:
            return
        elif response.status_code in [401, 403] and auth:
            raise AuthException(message=f"Failed to connect to auth at API (http {response.status_code})")
        else:
            raise GeneralAPIException(message=f"General API error caused by http code {response.status_code}")


class APIException(Exception):
    def __init__(self, message="", previous=None, next=None):
        if message:
            self.message = message
        if previous:
            self.previous = previous
        if next:
            self.next = next


class ConnectionException(APIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class AuthException(APIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NoTokenException(APIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GeneralAPIException(APIException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

