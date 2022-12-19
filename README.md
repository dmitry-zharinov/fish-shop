# Telegram Shop Bot
Чат-бот с интеграцией с CMS магазина Elastic Path. В боте-магазине можно посмотреть витрину, добавить товары в корзину и оставить контакты для связи.

[Пример бота](https://t.me/dw_dvmn_shop_bot)

### Требования
Для развертывания приложения необходимо зарегистрировать:
- [Базу данных Redis](https://app.redislabs.com)
- [Магазин с товарами Elastic Path](https://www.elasticpath.com/). Используется версия legacy-API (v2). Продукты на данный момент добавляются через  запросы к API: [подробнее](https://documentation.elasticpath.com/commerce-cloud/docs/api/catalog/products/index.html).
Необходимо сгенерировать ключ приложения на странице Settings → Application Keys в [личном кабинете](https://euwest.cm.elasticpath.com).

### Установка
1. Предварительно должен быть установлен Python3.
2. Для установки зависимостей, используйте команду pip (или pip3, если есть конфликт с Python2) :
```shell
pip install -r requirements.txt
```
3. Для Telegram: необходимо [зарегистрировать бота и получить его API-токен](https://telegram.me/BotFather)
4. В директории скрипта создайте файл `.env` и укажите в нём следующие данные:

- `CLIENT_SECRET` — CLIENT_SECRET из ключа приложения в [Elastic Path](https://euwest.cm.elasticpath.com/application-keys)
- `CLIENT_ID` — CLIENT_ID из ключа приложения в [Elastic Path](https://euwest.cm.elasticpath.com/application-keys)
- `TELEGRAM_TOKEN` — токен для Telegram-бота, полученный от Bot Father.
- `ADMIN_USER` — id чата Telegram, куда будут отправляться логи (можно узнать у @userinfobot).
- `DATABASE_HOST` — url подключения к базе данных Redis, можно получить [в личном кабинете](https://app.redislabs.com) после регистрации 
- `DATABASE_PORT` — порт базы данных Redis
- `DATABASE_PASSWORD` — пароль для подключения к базе данных Redis

Пример:
```
CLIENT_SECRET=9744ec2463960d82d135rth72ee111112254
CLIENT_ID=1a595c25crthrth5598wcebe85hrtdc8b500
TELEGRAM_TOKEN=12332454:AAFLMWGT4otu_8_YH5_k4J_6ssGRfvGdwq
DATABASE_HOST=redis-12345.c555.us-east-1-3.ec2.cloud.redislabs.com
DATABASE_PORT=13627
DATABASE_PASSWORD=TRHhEFJYTrehjtyjtjtLg
TELEGRAM_ADMIN_USER=55555555
```

### Запуск бота 
```shell
$ python bot.py
```
