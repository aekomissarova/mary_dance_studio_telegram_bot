
import main
import time
from datetime import datetime
import schedule
import db_manipulator as db

from apscheduler.schedulers.background import BackgroundScheduler


def job():
    now = str(datetime.now().strftime("%H:%M"))
    connection_to_database, connection = db.connect_to_database()
    connection = connection_to_database.cursor()
    db.create_users_table(connection_to_database, connection)
    db.create_cache_events_table(connection_to_database, connection)
    data = db.select_users_and_time(connection_to_database, connection)

    if data is not None:
        for item in data:
            if item[1] == now:
                main.notify(item[0], item[2])
    db.close_connection(connection_to_database, connection)


def scheduler_start():
    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    schedule.every().hour.at(":00").do(job)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
