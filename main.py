import db_manipulator as db

from datetime import datetime, timedelta

import API_inquirer as api
import JSON_parser as parser

from multiprocessing import Process

import telebot
from telebot import types

import scheduler

bot = telebot.TeleBot("TOKEN", threaded=False, parse_mode=None)


@bot.message_handler(commands=['number'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Введи свой номер телефона без +7")
    bot.register_next_step_handler(message, save_phone_number)


@bot.message_handler(commands=['password'])
def start_message(message):
    bot.send_message(message.chat.id, "Введи пароль от своего личного кабинета MaryDance")
    bot.register_next_step_handler(message, save_password)


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "Привет!\nВведи /number для ввода или изменения номера телефона\n"
                                      "Введи /schedule для выбора времени напоминаний\n"
                                      "Введи /password для ввода пароля от личного кабинета\n"
                                      "Введи /today для просмотра занятий на сегодня")


@bot.message_handler(commands=['today'])
def today(message):
    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    now = datetime.now()

    if db.is_phone_number_exists(connection, message.from_user.id) is not None:
        db.create_cache_events_table(connection_to_database, connection)

        if db.get_cache_data_about_events(connection_to_database, connection, message.from_user.id) is not None:
            time, cache = db.get_cache_data_about_events(connection_to_database, connection, message.from_user.id)

            if (now - time) < timedelta(hours=1):
                send_long_message(cache, message.chat.id)

            else:
                phone_number, password = db.get_phone_number_and_password(connection_to_database, connection, message.from_user.id)
                token = api.login_in_api(phone_number, password)
                events = api.get_events(token)
                events_today = parser.events_for_today(events)
                db.update_cache_data_about_events(connection_to_database, connection, message.from_user.id,
                                                  events_today,
                                                  now)
                send_long_message(events_today, message.chat.id)

        else:
            phone_number, password = db.get_phone_number_and_password(connection_to_database, connection, message.from_user.id)
            token = api.login_in_api(phone_number,password)
            events = api.get_events(token)
            events_today = parser.events_for_today(events)
            db.save_cache_data_about_events(connection_to_database, connection, message.from_user.id, events_today, now)
            send_long_message(events_today, message.chat.id)

    else:
        bot.send_message(message.chat.id,
                         "У меня нет данных, чтобы найти для тебя информацию.\n Введи /number для ввода или изменения номера телефона")
    db.close_connection(connection_to_database, connection)


@bot.message_handler(commands=['schedule'])
def schedule(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    button07 = types.KeyboardButton('07:00')
    button08 = types.KeyboardButton('08:00')
    button09 = types.KeyboardButton('09:00')
    button10 = types.KeyboardButton('10:00')
    button11 = types.KeyboardButton('11:00')
    button12 = types.KeyboardButton('12:00')
    button13 = types.KeyboardButton('13:00')
    button14 = types.KeyboardButton('14:00')
    button15 = types.KeyboardButton('15:00')
    button16 = types.KeyboardButton('16:00')
    button17 = types.KeyboardButton('17:00')
    button18 = types.KeyboardButton('18:00')
    keyboard.add(button07, button08, button09, button10, button11, button12, button13, button14, button15, button16,
                 button17, button18)
    bot.send_message(message.chat.id, "Выбери время ежедневных напоминаний:", reply_markup=keyboard)
    bot.register_next_step_handler(message, save_notification_time)


@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.from_user.id
    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    db.delete_user(connection_to_database, connection, user_id)
    db.close_connection(connection_to_database, connection)


def save_password(message):
    password = message.text
    user_id_from_bot = message.from_user.id
    chat_id = message.chat.id

    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    db.save_password_and_user_id(connection_to_database, connection, password, user_id_from_bot, chat_id)
    db.close_connection(connection_to_database, connection)

    bot.send_message(message.chat.id, f"Я сохранил твой пароль. Не волнуйся, он зашифрован!")


@bot.message_handler(content_types=['text'])
def any_text_message(message):
    bot.send_message(message.chat.id, "Я тебя не понимаю, введи /help чтобы посмотреть, что я умею")


def save_phone_number(message):
    phone_number = message.text
    user_id_from_bot = message.from_user.id
    chat_id = message.chat.id

    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    db.save_phone_number_and_user_id(connection_to_database, connection, phone_number, user_id_from_bot, chat_id)
    db.close_connection(connection_to_database, connection)

    bot.send_message(message.chat.id, f"Я сохранил твой номер {phone_number}")


def save_notification_time(message):
    time = message.text
    user_id_from_bot = message.from_user.id
    chat_id = message.chat.id

    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    db.save_notification_time_and_user_id(connection_to_database, connection, time, user_id_from_bot, chat_id)
    db.close_connection(connection_to_database, connection)

    bot.send_message(message.chat.id, f"Буду напоминать о занятиях каждый день в {time}")


def send_long_message(message, message_id):
    if len(message) > 4096:
        for x in range(0, len(message), 4096):
            bot.send_message(message_id, message[x:x + 4096])
    else:
        bot.send_message(message_id, message)


def bot_polling():
    bot.infinity_polling()


def notify(user_id, chat_id):
    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    phone_number, password = db.get_phone_number_and_password(connection_to_database, connection, user_id)
    token = api.login_in_api(phone_number, password)
    events = api.get_events(token)
    events_today = parser.events_for_today(events)
    now = datetime.now()
    db.update_cache_data_about_events(connection_to_database, connection, user_id,
                                      events_today,
                                      now)
    send_long_message(events_today, chat_id)
    db.close_connection(connection_to_database, connection)


if __name__ == '__main__':
    p1 = Process(target=bot_polling)
    p2 = Process(target=scheduler.scheduler_start)
    p1.start()
    p2.start()
