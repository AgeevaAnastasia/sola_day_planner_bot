from db import SQLiteClient
from TelegramRequest import TelegramRequest
from envparse import Env
from logging import getLogger, StreamHandler

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel("INFO")

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.str("ADMIN_CHAT_ID")


class Reminder:
    GET_OVERDUE_TASKS = """
        SELECT task_name, task_description, deadline, done, user_id
        FROM tasks WHERE deadline < date('now');
    """

    GET_URGENTLY_TASKS = """
            SELECT task_name, task_description, deadline, done, user_id
            FROM tasks WHERE deadline BETWEEN date('now') AND date ('now', '+1 day');
        """

    GET_SOON_TASKS = """
            SELECT task_name, task_description, deadline, done, user_id
            FROM tasks WHERE deadline BETWEEN date('now', '+2') AND date ('now', '+3 day');
        """

    GET_NOT_URGENTLY_TASKS = """
            SELECT task_name, task_description, deadline, done, user_id
            FROM tasks WHERE deadline > date('now', '+3 day');
        """

    def __init__(self, telegram_request: TelegramRequest, sqlite_client: SQLiteClient):
        self.telegram_request = telegram_request
        self.sqlite_client = sqlite_client
        self.setted_up = False

    def setup(self):
        self.sqlite_client.create_conn()
        self.setted_up = True

    def shutdown(self):
        self.sqlite_client.close_conn()
        self.setted_up = False

    def notify_overdue(self, tasks: list):
        for task in tasks:
            user = int(task[4])
            if task[3] == 0:
                task = f'{task[0]}\n{task[1]}\n\nдо {task[2]}'
                result = self.telegram_request.post(method='sendMessage', params={'text': f'ПРОСРОЧЕНО! \n\n{task}',
                                                                                  'chat_id': user})
                logger.info(result)

    def notify_urgently(self, tasks: list):
        for task in tasks:
            user = int(task[4])
            if task[3] == 0:
                task = f'{task[0]}\n{task[1]}\n\nдо {task[2]}'
                result = self.telegram_request.post(method='sendMessage', params={'text': f'ОЧЕНЬ СРОЧНО: \n\n{task}',
                                                                                  'chat_id': user})
                logger.info(result)

    def notify_soon(self, tasks: list):
        for task in tasks:
            user = int(task[4])
            if task[3] == 0:
                task = f'{task[0]}\n{task[1]}\n\nдо {task[2]}'
                result = self.telegram_request.post(method='sendMessage',
                                                    params={'text': f'Срок исполнения близок: \n\n{task}',
                                                            'chat_id': user})
                logger.info(result)

    def notify_not_urgently(self, tasks: list):
        for task in tasks:
            user = int(task[4])
            if task[3] == 0:
                task = f'{task[0]}\n{task[1]}\n\nдо {task[2]}'
                result = self.telegram_request.post(method='sendMessage',
                                                    params={'text': f'Срок задачи еще не подошёл: \n\n{task}',
                                                            'chat_id': user})
                logger.info(result)

    def execute(self):
        tasks_overdue = self.sqlite_client.execute_select_query(self.GET_OVERDUE_TASKS)
        tasks_urgently = self.sqlite_client.execute_select_query(self.GET_URGENTLY_TASKS)
        tasks_soon = self.sqlite_client.execute_select_query(self.GET_SOON_TASKS)
        tasks_not_urgently = self.sqlite_client.execute_select_query(self.GET_NOT_URGENTLY_TASKS)
        if tasks_overdue:
            self.notify_overdue(tasks_overdue)
        if tasks_urgently:
            self.notify_urgently(tasks_urgently)
        if tasks_soon:
            self.notify_soon(tasks_soon)
        if tasks_not_urgently:
            self.notify_not_urgently(tasks_not_urgently)

    def __call__(self, *args, **kwargs):
        if not self.setted_up:
            logger.error('Resources in worker has not been set up!')
            return
        self.execute()


if __name__ == '__main__':
    sqlite_client = SQLiteClient('tasks.db')
    telegram_request = TelegramRequest(token=TOKEN, constant_url='http://api.telegram.org')
    reminder = Reminder(sqlite_client=sqlite_client, telegram_request=telegram_request)
    reminder.setup()
    reminder()
