import logging
import os
from time import time

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
from bot_logging import TelegramLogsHandler

from moltin import (
    add_product_to_cart,
    download_product_image,
    get_access_token,
    get_cart_items,
    get_product,
    get_products,
    create_customer,
    get_cart,
    remove_product_from_cart,
)

_database = None
logger = logging.getLogger("tg-bot")


def start(update, context):
    db = context.bot_data["db"]
    token = db.get("access_token").decode("utf-8")
    products = get_products(token)
    keyboard = [
        [InlineKeyboardButton(product["name"], callback_data=product["id"])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🛍 Выберите товар:", reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(update, context):
    db = context.bot_data["db"]
    token = db.get("access_token").decode("utf-8")
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
    )
    callback = update.callback_query.data
    product_id = callback
    product = get_product(product_id, token)
    image_id = product["relationships"]["main_image"]["data"]["id"]

    product_image = download_product_image(image_id, token)
    product_description = f"""
    <b>{product["name"]}</b>\n\n
    {product["description"]}\n\n
    <i><b>Цена: {product['meta']['display_price']['with_tax']['formatted']}
    </b></i>
    """

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Добавить в корзину", callback_data=f"{product_id}~1"
                ),
            ],
            [InlineKeyboardButton("🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton("🔙 Назад", callback_data="go_back")],
        ]
    )

    with open(product_image, "rb") as photo:
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo,
            caption=product_description,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    return "HANDLE_DESCRIPTION"


def handle_description(update, context):
    db = context.bot_data["db"]
    token = db.get("access_token").decode("utf-8")
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
    products = get_products(token)
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
    add_product_to_cart(token, cart_id, product["sku"], int(quantity))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Товар {product['name']} добавлен в корзину!",
    )


def show_cart_items(update, context, token):
    cart_id = update.effective_chat.id
    cart = get_cart(token, cart_id)
    cart_items = get_cart_items(token, cart_id)

    text = list()
    text.append('<b>🛒 Ваша корзина:</b>\n')
    cart_text = [
        f"<b>{num+1}. {product['name']}</b>\n"
        f"{product['meta']['display_price']['with_tax']['unit']['formatted']}"
        f"за шт.\n"
        f"{product['quantity']} шт. в корзине на сумму "
        f"{product['meta']['display_price']['with_tax']['value']['formatted']}"
        f"\n\n"
        for num, product in enumerate(cart_items)
    ]
    text.extend(cart_text)
    text.append(
        f"<b>Итого: "
        f"{cart['meta']['display_price']['with_tax']['formatted']}</b>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f"🗑 Убрать {product['name']}",
                callback_data=product["id"]
            )
        ]
        for product in cart_items
    ]
    keyboard.append([InlineKeyboardButton("✅ К оплате", callback_data="pay")])
    keyboard.append(
        [InlineKeyboardButton("🔙 В меню", callback_data="go_back")])

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="".join(text),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def handle_cart(update, context):
    db = context.bot_data["db"]
    token = db.get("access_token").decode("utf-8")
    callback = update.callback_query.data

    if callback == "go_back":
        show_items_menu(update, context, token)
        return "HANDLE_MENU"
    elif callback == "pay":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📧 Пожалуйста, укажите вашу почту:",
        )
        return "WAITING_EMAIL"
    else:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
        )
        cart_id = update.effective_chat.id
        remove_product_from_cart(token, cart_id, callback)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Товар удалён из корзины!",
        )
        return "HANDLE_CART"


def handle_email(update, context):
    db = context.bot_data["db"]
    token = db.get("access_token").decode("utf-8")
    email = update.message.text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Вы прислали мне эту почту: {email}",
    )

    create_customer(email, token)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Заказ передан менеджеру, он свяжется с вами в ближайшее время.",
    )

    return "START"


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
        "WAITING_EMAIL": handle_email,
    }
    state_handler = states_functions[user_state]
    try:
        token_expires = int(db.get("access_token_expires").decode("utf-8"))
        if token_expires < time():
            client_id = db.get("client_id").decode("utf-8")
            client_secret = db.get("client_secret").decode("utf-8")
            token = get_access_token(client_id, client_secret)
            db.set("access_token", token["access_token"])
            db.set("access_token_expires", token["expires"])

        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logging.exception(err)


def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(
            host=database_host, port=database_port, password=database_password
        )
    return _database


if __name__ == "__main__":
    load_dotenv()

    tg_token = os.getenv("TELEGRAM_TOKEN")
    admin_user = os.getenv("TELEGRAM_ADMIN_USER")

    logging.basicConfig(level=logging.INFO)
    logger.addHandler(
        TelegramLogsHandler(tg_token, admin_user)
    )

    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    access_token = get_access_token(client_id, client_secret)

    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    db = redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password)
    db.set("access_token", access_token["access_token"])
    db.set("access_token_expires", access_token["expires"])
    db.set("client_id", client_id)
    db.set("client_secret", client_secret)

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["db"] = db
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    updater.start_polling()
