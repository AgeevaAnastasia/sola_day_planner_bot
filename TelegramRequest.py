import requests
import telebot
from envparse import Env

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")
bot = telebot.TeleBot(token=TOKEN)


class TelegramRequest:
    def __init__(self, token: str, constant_url: str):
        self.token = token
        self.constant_url = constant_url

    def make_url(self, method: str) -> str:
        url = f'{self.constant_url}/bot{self.token}/'
        if method is not None:
            url += method
        return url

    def post(self, method: str = None, params: dict = None, data: dict = None) -> object:
        url = self.make_url(method)
        response = requests.post(url, params=params, data=data)
        return response.json()


if __name__ == '__main__':
    telegram_request = TelegramRequest(token=TOKEN, constant_url='https://api.telegram.org')
    my_params = {'chat_id': ADMIN_CHAT_ID, 'text': 'sampleTEXT'}
    print(telegram_request.post(method='sendMessage', params=my_params))
