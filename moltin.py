import os
import logging

import requests
from dotenv import load_dotenv
import json


def get_access_token(client_id, client_secret):
    endpoint = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(endpoint, data=data)
    response.raise_for_status()
    return response.json()['access_token']


def get_products(token):
    endpoint = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product(product_id, token):
    endpoint = f'https://api.moltin.com/pcm/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_image(product_id, token):
    endpoint = f'https://api.moltin.com/pcm/products/{product_id}/relationships/main-image'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    logging.info(f'endpoint: {endpoint}')
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def download_product_image(image_id, token):
    endpoint = f'https://api.moltin.com/v2/files/{image_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)

    response.raise_for_status()
    decoded_response = response.json()['data']

    image_url = decoded_response['link']['href']
    image_name = decoded_response['file_name']

    response = requests.get(image_url)
    response.raise_for_status()
    with open(image_name, 'wb') as file:
        file.write(response.content)
    return image_name


def get_file_by_id(file_id, token):
    endpoint = f'https://api.moltin.com/v2/files/{file_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.post(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def create_cart(token, cart_name):
    endpoint = 'https://api.moltin.com/v2/carts'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    data = {
        'data': {
            'name': cart_name,
        }
    }
    response = requests.post(endpoint, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['data']


def get_cart(token, cart_id):
    endpoint = f'https://api.moltin.com/v2/carts/{cart_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'include': 'items'
    }
    response = requests.get(endpoint, headers=headers, params=payload)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_cart(token, cart_id, product):
    endpoint = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    product_item = {
        'data': {
            'type': 'custom_item',
            'name': product['attributes']['name'],
            'sku': product['attributes']['sku'],
            'description': product['attributes']['description'],
            'quantity': 1,
            "price": {
                "amount": 500
            }
        }
    }

    custom_item = {
      "data": {
        "type": "custom_item",
        "name": "My Custom Item",
        "sku": "my-custom-item",
        "description": "My first custom item!",
        "quantity": 1,
        "price": {
          "amount": 10000
        }
      }
    }
    response = requests.post(
        endpoint,
        headers=headers,
        json=custom_item)
    response.raise_for_status()
    return response.json()


def main():
    client_id = os.getenv('CLIENT_ID'),
    client_secret = os.getenv('CLIENT_SECRET'),
    # Получить токен
    token = get_access_token(client_id, client_secret)
    logging.info(f'token: {token}')
    products = get_products(token)
    #product_1 = products[0]

    # Создать корзину
    #cart = create_cart(token, 'test_cart')
    # Добавить продукт в корзину
    #add_product_to_cart(token, cart['id'], product_1)
    #refreshed_cart = get_cart(token, cart['id'])
    #print(json.dumps(refreshed_cart, sort_keys=True, indent=4))


if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    main()
