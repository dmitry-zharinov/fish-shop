import logging
import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from moltin import (
    add_product_id_to_cart,
    download_product_image,
    get_access_token,
    get_cart_items,
    get_product,
    get_products,
    get_cart,
    remove_product_from_cart,
)

_database = None
logger = logging.getLogger("tg-bot")


def start(update, context):
    db = context.bot_data["db"]
    moltin_token = db.get("moltin_token").decode("utf-8")
    products = get_products(moltin_token)
    keyboard = [
        [InlineKeyboardButton(product["name"], callback_data=product["id"])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите товар:", reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(update, context):
    db = context.bot_data["db"]
    moltin_token = db.get("moltin_token").decode("utf-8")
    # price_book_id = db.get('price_book_id').decode("utf-8")
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
    )
    callback = update.callback_query.data
    product_id = callback
    product = get_product(product_id, moltin_token)
    image_id = product["relationships"]["main_image"]["data"]["id"]

    product_image = download_product_image(image_id, moltin_token)
    product_description = product["description"]

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "ДОбавить в корзину", callback_data=f"{product_id}~1"
                ),
            ],
            [InlineKeyboardButton("Корзина", callback_data="cart")],
            [InlineKeyboardButton("Назад", callback_data="go_back")],
        ]
    )

    with open(product_image, "rb") as photo:
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo,
            caption=product_description,
            reply_markup=reply_markup,
        )
    return "HANDLE_DESCRIPTION"


def handle_description(update, context):
    db = context.bot_data["db"]
    token = db.get("moltin_token").decode("utf-8")
    callback = update.callback_query.data

    if callback == "cart":
        show_cart_items(update, context, token)
        return "HANDLE_CART"
    elif callback != "go_back":
        add_item_to_cart(update, context, token)
        return "HANDLE_DESCRIPTION"
    else:
        show_items_menu(update, context, token)
        return "HANDLE_MENU"


def show_items_menu(update, context, token):
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
    )
    products = get_products(moltin_token)
    keyboard = [
        [InlineKeyboardButton(product["name"], callback_data=product["id"])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите товар:",
        reply_markup=reply_markup,
    )


def add_item_to_cart(update, context, token):
    callback = update.callback_query.data
    product_id, quantity = callback.split("~")
    product = get_product(product_id, token)
    cart_id = update.effective_chat.id
    add_product_id_to_cart(token, cart_id, product["sku"], int(quantity))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Товар {product['name']} добавлен в корзину!",
    )


def show_cart_items(update, context, token):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="<b>Ваша корзина:</b>",
        parse_mode=ParseMode.HTML,
    )

    cart_id = update.effective_chat.id
    cart = get_cart(token, cart_id)
    cart_items = get_cart_items(token, cart_id)
    text = [
        f"""{num+1}. {product['name']}
            {product['meta']['display_price']['with_tax']['unit']['formatted']} за шт.
            {product['quantity']} шт. в корзине на сумму {product['meta']['display_price']['with_tax']['value']['formatted']}\n\n"""
        for num, product in enumerate(cart_items)
    ]
    text.append(
        f"<b>Итого: {cart['meta']['display_price']['with_tax']['formatted']}</b>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f"Убрать из корзины {product['name']}", callback_data=product["id"]
            )
        ]
        for product in cart_items
    ]
    keyboard.append([InlineKeyboardButton("В меню", callback_data="go_back")])

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="".join(text),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def handle_cart(update, context):
    db = context.bot_data["db"]
    token = db.get("moltin_token").decode("utf-8")
    callback = update.callback_query.data

    if callback == "go_back":
        show_items_menu(update, context, token)
        return "HANDLE_MENU"
    else:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
        )
        cart_id = update.effective_chat.id
        remove_product_from_cart(token, cart_id, callback)
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Товар удалён из корзины!"
        )
        return "HANDLE_CART"


def handle_users_reply(update, context):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    elif user_reply == "go_back":
        user_state = "HANDLE_DESCRIPTION"
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description,
        "HANDLE_CART": handle_cart,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(
            host=database_host, port=database_port, password=database_password
        )
    return _database


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    moltin_token = get_access_token(client_id, client_secret)
    logging.info(f"token: {moltin_token}")

    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    db = redis.Redis(host=database_host, port=database_port, password=database_password)
    db.set("moltin_token", moltin_token)
    # price_book_id = os.getenv('PRICE_BOOK_ID')
    # db.set('price_book_id', price_book_id)

    updater = Updater(os.getenv("TELEGRAM_TOKEN"))
    dispatcher = updater.dispatcher
    dispatcher.bot_data["db"] = db
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    updater.start_polling()
