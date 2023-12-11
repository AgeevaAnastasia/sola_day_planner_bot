from logging import getLogger, StreamHandler
import datetime
import time
from envparse import Env

from db import SQLiteClient
from TelegramRequest import TelegramRequest
from worker import Reminder

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel('INFO')
env = Env()
TOKEN = env.str('TOKEN')
FROM_TIME = env.str('FROM_TIME')
TO_TIME = env.str('TO_TIME')
REMINDER_PERIOD = env.int('REMINDER_PERIOD', default=3600)
SLEEP_PERIOD = env.int('SLEEP_PERIOD', default=3600)

sqlite_client = SQLiteClient('tasks.db')
telegram_request = TelegramRequest(token=TOKEN, constant_url='https://api.telegram.org')
reminder = Reminder(sqlite_client=sqlite_client, telegram_request=telegram_request)
reminder.setup()

start_time = datetime.datetime.strptime(FROM_TIME, '%H:%M').time()
end_time = datetime.datetime.strptime(TO_TIME, '%H:%M').time()

while True:
    now_time = datetime.datetime.now().time()
    if start_time <= now_time <= end_time:
        reminder()
        time.sleep(REMINDER_PERIOD)
    else:
        time.sleep(SLEEP_PERIOD)
