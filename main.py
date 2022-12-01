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
    endpoint = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_cart(token, product):
    cart_id = '123'
    endpoint = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    data = {
      'data': {
          'id': product,
          'type': 'cart_item',
        }
    }
    response = requests.post(endpoint, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def main():
    client_id = os.getenv('CLIENT_ID'),
    client_secret = os.getenv('CLIENT_SECRET'),

    #token = os.getenv('ACCESS_TOKEN')
    token = get_access_token(client_id, client_secret)
    #print(token)
    products = get_products(token)
    product_1 = products[0]
    
    test_product = {
        "data": {
            "id": "df32387b-6ce6-4802-9b90-1126a5c5a54f",
            "type": "cart_item",
            "quantity": 1,
            "custom_inputs": {
              "name": {
                "T-Shirt Front": "Jane",
                "T-Shirt Back": "Jane Doe's Dance Academy"
               }
            }
        }
    }
    
    print(f'Add product {product_1["id"]} to cart')
    cart = add_product_to_cart(token, test_product)
    print(cart)

if __name__ == '__main__':
    load_dotenv()  
    main()
