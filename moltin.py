import logging
import os

import requests
from dotenv import load_dotenv


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
    endpoint = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product(product_id, token):
    endpoint = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_image(product_id, token):
    endpoint = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
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
    image_path = os.path.join('tmp', image_name)

    response = requests.get(image_url)
    response.raise_for_status()
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return image_path


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
    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()['data']


def get_cart_items(token, cart_id):
    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_id}/items',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()['data']


def add_product_id_to_cart(token, cart_id, product_sku, quantity):
    endpoint = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    product_item = {
        'data': {
            'type': 'cart_item',
            'sku': product_sku,
            'quantity': quantity,
        }
    }
    response = requests.post(
        endpoint,
        headers=headers,
        json=product_item)
    response.raise_for_status()
    return response.json()


def add_product_to_cart(token, cart_id, product_sku, quantity, name):
    logging.info(f'add_product_to_cart')
    endpoint = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    #product_item = {
    #    'data': {
    #        'type': 'custom_item',
    #        'name': product['attributes']['name'],
    #        'sku': product_sku,
    #        'description': product['attributes']['description'],
    #        'quantity': 1,
    #        "price": {
    #            "amount": 500
    #        }
    #    }
    #}

    custom_item = {
      "data": {
        "type": "custom_item",
        "name": name,
        "sku": product_sku,
        #"description": "My first custom item!",
        "quantity": quantity,
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



def remove_product_from_cart(token, cart_id, product_id):
    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    response.raise_for_status()
    return response.json()


def get_price_book_prices(token, price_book_id):
    response = requests.get(
        f'https://api.moltin.com/pcm/pricebooks/{price_book_id}/prices/',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()['data']


def get_product_price(token, price_book_id, product_sku):
    prices = get_price_book_prices(token, price_book_id,)
    price_id = None
    for price in prices:
        if price['sku'] == product_sku:
            price_id = price['id']

    if price_id is None:
        return

    response = requests.get(
        f'https://api.moltin.com/pcm/pricebooks/{price_book_id}/prices/{price_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()['data']


def get_product_stock(token, product_id):
    response = requests.get(
        f'https://api.moltin.com/v2/inventories/{product_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()['data']


def main():
    client_id = os.getenv('CLIENT_ID'),
    client_secret = os.getenv('CLIENT_SECRET'),
    # Получить токен
    token = get_access_token(client_id, client_secret)
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
