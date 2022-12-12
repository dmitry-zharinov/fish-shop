import logging
import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from moltin import (get_access_token, get_file_by_id, get_product,
                    download_product_image, get_products)

_database = None
logger = logging.getLogger('tg-bot')


def start(update, context):
    db = context.bot_data['db']
    moltin_token = db.get('moltin_token').decode("utf-8")
    products = get_products(moltin_token)
    keyboard = [
        [InlineKeyboardButton(product['attributes']['name'],
                              callback_data=product['id'])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_menu(update, context):
    db = context.bot_data['db']
    moltin_token = db.get('moltin_token').decode('utf-8')
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
    )
    callback = update.callback_query.data
    product_id = callback
    product = get_product(product_id, moltin_token)
    image_id = product['relationships']['main_image']['data']['id']
    logging.info(f'image_id: {image_id}')
    product_image = download_product_image(image_id, moltin_token)
    logging.info(f'product_image: {product_image}')

    product_description = product['attributes']['description']
    with open(product_image, 'rb') as photo:
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo,
            caption=product_description,
        )
    return 'HANDLE_MENU'


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
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
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
        _database = redis.Redis(host=database_host,
                                port=database_port,
                                password=database_password)
    return _database


if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    moltin_token = get_access_token(client_id, client_secret)
    logging.info(f'token: {moltin_token}')

    database_password = os.getenv('DATABASE_PASSWORD')
    database_host = os.getenv('DATABASE_HOST')
    database_port = os.getenv('DATABASE_PORT')
    db = redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password
    )
    db.set('moltin_token', moltin_token)

    updater = Updater(os.getenv('TELEGRAM_TOKEN'))
    dispatcher = updater.dispatcher
    dispatcher.bot_data['db'] = db
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
