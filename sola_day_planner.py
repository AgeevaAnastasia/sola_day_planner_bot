import telebot
from telebot.types import Message
from datetime import datetime, timedelta
from envparse import Env
from TelegramRequest import TelegramRequest
from db import TaskAction, SQLiteClient
from logging import getLogger, StreamHandler, basicConfig

FORMAT = '{levelname:<8} - {asctime}'
basicConfig(format=FORMAT, style='{', level='INFO')
logger = getLogger(__name__)
logger.addHandler(StreamHandler())
# logger.setLevel("INFO")

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")
default_bot = telebot.TeleBot(token=TOKEN)


class MyBot(telebot.TeleBot):
    def __init__(self, telegram_request: TelegramRequest, task_action: TaskAction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_request = telegram_request
        self.task_action = task_action

    def setup_resources(self):
        self.task_action.setup()

    def shutdown_resources(self):
        self.task_action.shutdown()

    def shutdown(self):
        self.shutdown_resources()


telegram_request = TelegramRequest(token=TOKEN, constant_url='https://api.telegram.org')
task_action = TaskAction(SQLiteClient('tasks.db'))
bot = MyBot(token=TOKEN, telegram_request=telegram_request, task_action=task_action)


@bot.message_handler(commands=['new_task'])
def add_task(msg) -> None:
    message = bot.send_message(chat_id=msg.chat.id, text='Введите название, описание и срок выполнения задачи через //')
    bot.register_next_step_handler(message, read_task)


def read_task(message: Message):
    txt = message.text
    txt = txt.split('//')
    txt.append('')
    txt.append('')
    txt.append('')
    if txt[0] == '':
        bot.send_message(message.chat.id, 'Введите название, описание и срок выполнения задачи через //')
    elif txt[1] == '':
        bot.send_message(message.chat.id, 'Введите название, описание и срок выполнения задачи через //')
    elif txt[2] == '':
        bot.send_message(message.chat.id, 'Введите название, описание и срок выполнения задачи через //')
    else:
        task_name = txt[0]
        task_description = txt[1]
        deadline = txt[2]
        task_id = task_action.find_id() + 1
        creation_date = datetime.today().strftime('%Y-%m-%d')
        user_id = message.chat.id
        create_new_task = False

        task = bot.task_action.get_task_by_name(task_name=task_name, user_id=user_id)
        if not task:
            print(user_id)
            bot.task_action.create_task(task_id=task_id, task_name=task_name,
                                        task_description=task_description, creation_date=creation_date,
                                        deadline=deadline, done=0, user_id=user_id)
            create_new_task = True
        bot.reply_to(message=message, text=f'Задача с именем {task_name} {"уже" if not create_new_task else ""} '
                                           f'была создана {"ранее" if not create_new_task else ""}')


@bot.message_handler(commands=['find_task'])
def find_task(msg) -> None:
    message = bot.send_message(chat_id=msg.chat.id, text='Введите название задачи')
    bot.register_next_step_handler(message, find_task_name)


def find_task_name(message: Message):
    task = bot.task_action.get_task_by_name(task_name=message.text, user_id=message.chat.id)
    if task:
        text = f'{task[1]}\n{task[2]}\nВыполнить до: {task[4]}\n'
        bot.reply_to(message=message, text=text)
    else:
        bot.reply_to(message=message, text=f'Задача с именем {message.text} не найдена')


@bot.message_handler(commands=['done_task'])
def done_task(msg) -> None:
    message = bot.send_message(chat_id=msg.chat.id, text='Введите название задачи')
    bot.register_next_step_handler(message, make_task_done)


def make_task_done(message):
    task = bot.task_action.get_task_by_name(task_name=message.text, user_id=message.chat.id)
    if task:
        bot.task_action.done_task(task_name=task[1], user_id=message.chat.id)
        bot.reply_to(message=message, text=f'Задача {task[1]} помечена как выполненная')
    else:
        bot.reply_to(message=message, text=f'Задача с именем {task[1]} не найдена')


@bot.message_handler(commands=['today'])
def today(msg) -> None:
    tasks = bot.task_action.get_task_by_deadline(datetime.today().strftime('%Y-%m-%d'), user_id=msg.chat.id)
    bot.send_message(chat_id=msg.chat.id, text=f'Задачи на сегодня:\n ')
    if tasks:
        for task in tasks:
            if task[5] == 0:
                task = f'{task[1]}\n{task[2]}\n'
                bot.send_message(chat_id=msg.chat.id, text=f'{task}\n ')
    else:
        bot.send_message(chat_id=msg.chat.id, text='не найдены')


@bot.message_handler(commands=['tomorrow'])
def tomorrow(msg) -> None:
    tasks = bot.task_action.get_task_by_deadline((datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                                                 user_id=msg.chat.id)
    bot.send_message(chat_id=msg.chat.id, text=f'Задачи на завтра:\n ')
    if tasks:
        for task in tasks:
            if task[5] == 0:
                task = f'{task[1]}\n{task[2]}\n'
                bot.send_message(chat_id=msg.chat.id, text=f'{task}\n ')
    else:
        bot.send_message(chat_id=msg.chat.id, text='не найдены')


@bot.message_handler(commands=['undone'])
def undone(msg) -> None:
    tasks = bot.task_action.get_task_by_status(0, user_id=msg.chat.id)
    bot.send_message(chat_id=msg.chat.id, text=f'Невыполненные задачи:\n ')
    if tasks:
        for task in tasks:
            task = f'{task[1]}\n{task[2]}\nДо {task[4]}'
            bot.send_message(chat_id=msg.chat.id, text=f'{task}\n ')
    else:
        bot.send_message(chat_id=msg.chat.id, text='не найдены')


@bot.message_handler(commands=['done'])
def done(msg) -> None:
    tasks = bot.task_action.get_task_by_status(1, user_id=msg.chat.id)
    bot.send_message(chat_id=msg.chat.id, text=f'Выполненные задачи:\n ')
    if tasks:
        for task in tasks:
            task = f'{task[1]}\n{task[2]}\nДо {task[4]}'
            bot.send_message(chat_id=msg.chat.id, text=f'{task}\n ')
    else:
        bot.send_message(chat_id=msg.chat.id, text='не найдены')


def make_err_msg(err: Exception) -> str:
    return f'Возникла ошибка {err.__class__}: {err} в {datetime.now()}'


while True:
    try:
        bot.setup_resources()
        bot.polling()
    except Exception as e:
        error_msg = make_err_msg(e)
        my_params = {'text': error_msg,
                     'chat_id': ADMIN_CHAT_ID}
        bot.telegram_request.post(method='sendMessage', params=my_params)
        logger.error(error_msg)
        bot.shutdown()
