import os
import requests


def get_access_token(client_id, client_secret):
    endpoint = "https://api.moltin.com/oauth/access_token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(endpoint, data=data)
    response.raise_for_status()
    return response.json()


def get_products(token):
    endpoint = "https://api.moltin.com/v2/products"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def get_product(product_id, token):
    endpoint = f"https://api.moltin.com/v2/products/{product_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def download_product_image(image_id, token):
    endpoint = f"https://api.moltin.com/v2/files/{image_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(endpoint, headers=headers)

    response.raise_for_status()
    image_metadata = response.json()["data"]

    image_url = image_metadata["link"]["href"]
    image_name = image_metadata["file_name"]
    image_path = os.path.join("tmp", image_name)

    response = requests.get(image_url)
    response.raise_for_status()
    with open(image_path, "wb") as file:
        file.write(response.content)
    return image_path


def create_customer(email, token):
    response = requests.post(
        "https://api.moltin.com/v2/customers",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "data": {
                "type": "customer",
                "name": email,
                "email": email,
            }
        },
    )
    response.raise_for_status()


def get_cart(token, cart_id):
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()["data"]


def get_cart_items(token, cart_id):
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}/items",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()["data"]


def add_product_to_cart(token, cart_id, product_sku, quantity):
    endpoint = f"https://api.moltin.com/v2/carts/{cart_id}/items"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    product_item = {
        "data": {
            "type": "cart_item",
            "sku": product_sku,
            "quantity": quantity,
        }
    }
    response = requests.post(endpoint, headers=headers, json=product_item)
    response.raise_for_status()
    return response.json()


def remove_product_from_cart(token, cart_id, product_id):
    response = requests.delete(
        f"https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    response.raise_for_status()
    return response.json()
