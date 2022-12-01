import os

import requests
from dotenv import load_dotenv


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["Authorization"] = f'Bearer {self.token}'
        return r


def get_access_token():
    data = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'grant_type': 'client_credentials',
    }
    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data=data)
    response.raise_for_status()
    return response


def get_products():
    url = 'https://api.moltin.com/pcm/products'
    token = os.getenv('ACCESS_TOKEN')

    response = requests.get(
        url,
        auth=BearerAuth(token),
        )
    response.raise_for_status()
    return response


def main():
    products = get_products().json()
    print(products)

if __name__ == '__main__':
    load_dotenv()  
    main()
