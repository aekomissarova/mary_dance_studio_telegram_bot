import psycopg2
import configparser

import base64


def connect_to_database():
    config = configparser.ConfigParser()
    config.read("configuration/config.ini")
    config.sections()

    connection_to_database = psycopg2.connect(
        host=config['DB']['host'],
        database=config['DB']['database'],
        user=config['DB']['user'],
        password=config['DB']['password'])

    connection = connection_to_database.cursor()
    return connection_to_database, connection


def create_users_table(connection_to_database, connection):
    connection.execute("set transaction read write")
    connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id SERIAL,
            phone_number text NOT NULL UNIQUE,
            user_id_from_bot INTEGER NOT NULL UNIQUE,
            chat_id INTEGER NOT NULL UNIQUE,
            login text,
            password bytea,
            notification_time text,
            PRIMARY KEY(id)
            )""")
    connection_to_database.commit()


def create_cache_events_table(connection_to_database, connection):
    connection.execute("set transaction read write")
    connection.execute("""CREATE TABLE IF NOT EXISTS cache_data (
            id SERIAL,
            user_id_from_bot INTEGER NOT NULL,
            cache text,
            date_time TIMESTAMP,
            PRIMARY KEY(id)
            )""")
    connection_to_database.commit()


def save_phone_number_and_user_id(connection_to_database, connection, phone_number, user_id, chat_id):
    create_users_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("""SELECT user_id_from_bot FROM users WHERE user_id_from_bot = (%s)""", (user_id,))

    if connection.fetchone() is not None:
        connection.execute("set transaction read write")
        connection.execute("UPDATE users SET phone_number = %s WHERE user_id_from_bot = (%s) ", (phone_number,
                                                                                                 user_id), )
        connection_to_database.commit()
    else:
        connection.execute("set transaction read write")
        connection.execute("INSERT INTO users(phone_number,user_id_from_bot, chat_id) VALUES (%s, %s, %s)",
                           (phone_number, user_id, chat_id))
        connection_to_database.commit()


def save_notification_time_and_user_id(connection_to_database, connection, time, user_id, chat_id):
    create_users_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("""SELECT user_id_from_bot FROM users WHERE user_id_from_bot = (%s)""", (user_id,))

    if connection.fetchone() is not None:
        connection.execute("set transaction read write")
        connection.execute("UPDATE users SET notification_time = %s WHERE user_id_from_bot = (%s) ", (time,
                                                                                                      user_id), )
        connection_to_database.commit()
    else:
        connection.execute("set transaction read write")
        connection.execute("INSERT INTO users(notification_time, user_id_from_bot, chat_id) VALUES (%s, %s, %s)",
                           (time, user_id, chat_id), )
        connection_to_database.commit()


def save_password_and_user_id(connection_to_database, connection, password, user_id, chat_id):
    conv_bytes = bytes(password, 'utf-8')
    encoded_str = base64.b64encode(conv_bytes)
    create_users_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("""SELECT user_id_from_bot FROM users WHERE user_id_from_bot = (%s)""", (user_id,))

    if connection.fetchone() is not None:
        connection.execute("set transaction read write")
        connection.execute("UPDATE users SET password = %s WHERE user_id_from_bot = (%s) ", (encoded_str,
                                                                                             user_id), )
        connection_to_database.commit()
    else:
        connection.execute("set transaction read write")
        connection.execute("INSERT INTO users(password, user_id_from_bot, chat_id) VALUES (%s, %s, %s)",
                           (encoded_str, user_id, chat_id), )
        connection_to_database.commit()


def is_phone_number_exists(connection, user_id):
    connection.execute("set transaction read write")
    connection.execute("""SELECT phone_number FROM users WHERE user_id_from_bot = (%s)""", (user_id,))
    return connection.fetchone()


def get_cache_data_about_events(connection_to_database, connection, user_id):
    create_cache_events_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("""SELECT date_time, cache FROM cache_data WHERE user_id_from_bot = (%s)""", (user_id,))
    return connection.fetchone()


def get_phone_number_and_password(connection_to_database, connection, user_id):
    create_cache_events_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("""SELECT phone_number, password FROM users WHERE user_id_from_bot = (%s)""", (user_id,))
    phone_number, enc_password = connection.fetchone()
    return phone_number, base64.b64decode(enc_password).decode()


def save_cache_data_about_events(connection_to_database, connection, user_id, cache, time):
    create_cache_events_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("INSERT INTO cache_data(user_id_from_bot, cache, date_time) VALUES (%s, %s, %s)",
                       (user_id, cache, time), )
    connection_to_database.commit()


def update_cache_data_about_events(connection_to_database, connection, user_id, cache, time):
    create_cache_events_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("UPDATE cache_data SET cache = %s, date_time =%s WHERE user_id_from_bot = %s",
                       (cache, time, user_id,), )
    connection_to_database.commit()


def select_users_and_time(connection_to_database, connection):
    create_cache_events_table(connection_to_database, connection)
    connection.execute("set transaction read write")
    connection.execute("""SELECT user_id_from_bot, notification_time, chat_id FROM users""")
    return connection.fetchall()


def delete_user(connection_to_database, connection, user_id):
    connection.execute("set transaction read write")
    connection.execute("DELETE FROM users WHERE user_id_from_bot = %s ", (user_id,))
    connection.execute("set transaction read write")
    connection.execute("DELETE FROM cache_data WHERE user_id_from_bot = %s ", (user_id,))
    connection_to_database.commit()


def close_connection(connection_to_database, connection):
    connection.close()
    connection_to_database.close()
