import argparse
import requests
import time

from functools import wraps
from random import random


def arg_parser():
    parser = argparse.ArgumentParser(
        description='Barbora Scheduler'
    )

    parser.add_argument(
        '--email',
        '-e',
        help='Tell me your email to use for login',
        required=True,
    )
    parser.add_argument(
        '--password',
        '-p',
        help='Tell me your password to use for login',
        required=True
    )
    parser.add_argument(
        '--botapikey',
        help='Tell me your telegram bot API key',
        required=True
    )
    parser.add_argument(
        '--botchatid',
        help='Tell me your telegram chat id',
        required=True
    )
    return vars(parser.parse_args())


def retry(allowed_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.Timeout),
          retry_count=3,
          base_delay=1,
          backoff=2):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for attempt in range(retry_count):
                try:
                    return f(*args, **kwargs)
                except allowed_exceptions:
                    pdelay = pow(backoff, attempt) * base_delay * (1 + random() / 4)
                    if attempt >= retry_count - 1:
                        raise
                    time.sleep(pdelay)
        return wrapper
    return decorator

@retry((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
def send_message(bot_token, bot_chat_id, message, **kwargs):
    requests.get(
        f'https://api.telegram.org/bot{bot_token}/sendMessage',
        params={
            'chat_id': bot_chat_id,
            'parse_mode': 'Markdown',
            'text': message
        },
        timeout=kwargs.get('timeout', (3, 30))
    )


class BarboraLt:

    def __init__(self, **kwargs):
        self.email = kwargs.get('email', '')
        self.__password = kwargs.get('password', '')

        self.session = requests.Session()
        self.session.headers.update({
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Authorization': 'Basic YXBpa2V5OlNlY3JldEtleQ==',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'DNT': '1',
            'Host': 'barbora.lt',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4026.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Dest': 'emtpy',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        self.session.verify = kwargs.get('verify', True)

        cookie_jar = requests.cookies.RequestsCookieJar()
        cookie_jar.set('region', 'barbora.lt', domain='.barbora.lt', path='/')

        self.session.cookies = cookie_jar

    @retry((requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def request(self, method, uri, **kwargs):
        return self.session.request(
            method,
            f'https://barbora.lt/{uri}',
            data=kwargs.get('data', None),
            headers=kwargs.get('headers', None),
            params=kwargs.get('params', None),
            timeout=kwargs.get('timeout', (3, 30))
        )

    def login(self):
        response = self.request(
            'POST',
            'api/eshop/v1/user/login',
            data={
                "email": self.email,
                "password": self.__password,
                "rememberMe": False
            },
            headers={
                'Origin': 'https://barbora.lt',
                'Referer': 'https://barbora.lt/'
            }
        )
        response.raise_for_status()
        return response

    def get_delivery_dates(self):
        response = self.request(
            'GET',
            'api/eshop/v1/cart/deliveries',
            headers={
                'Referer': 'https://barbora.lt/pristatymas'
            },
            timeout=(3,300)
        )
        response.raise_for_status()
        return response


if __name__ == '__main__':
    arguments = arg_parser()
    conn_hdl = BarboraLt(email=arguments.get('email'), password=arguments.get('password'))
    conn_hdl.login()
    barbora_resonse = conn_hdl.get_delivery_dates()
    if barbora_resonse.ok:
        delivery_matrix = barbora_resonse.json()['deliveries'][0]['params']['matrix']
        for day in delivery_matrix:
            for hour in day['hours']:
                if hour.get('available'):
                    send_message(arguments.get('botapikey'), arguments.get('botchatid'), f'{hour.get("deliveryTime")} :: {hour.get("available")}')