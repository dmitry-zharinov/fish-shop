import logging
import os

import redis
from dotenv import load_dotenv
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from main import get_access_token, get_products

_database = None
logger = logging.getLogger('tg-bot')


def start(update, context):
    db = context.bot_data["db"]
    moltin_token = db.get('moltin_token').decode("utf-8")
    #logger.info(f'moltin_token from db: {moltin_token}')
    products = get_products(moltin_token)
    logger.info(f'products: {products}')
    keyboard = [
        [InlineKeyboardButton(product['attributes']['name'],
                              callback_data=product['id'])]
        for product in products
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "ECHO"


def echo(update, context):
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


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
        user_state = db.get(chat_id).decode("utf-8")
    
    states_functions = {
        'START': start,
        'ECHO': echo
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
        print(chat_id)
        print(next_state)
    except Exception as err:
        print('Error')
        print(err)

def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


if __name__ == '__main__':
    load_dotenv()  
    logging.basicConfig(level=logging.INFO)

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    moltin_token = get_access_token(client_id, client_secret)

    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    db = redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password
    )
    db.set('moltin_token', moltin_token)

    updater = Updater(os.getenv('TELEGRAM_TOKEN'))
    dispatcher = updater.dispatcher
    dispatcher.bot_data["db"] = db
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
