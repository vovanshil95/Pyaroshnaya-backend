import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN')

MSG_WELLCOME_TEXT = "Привет! Я виртуальный помощник портала «Пиарошная», и сейчас мы быстро пройдем регистрацию или восстановим пароль!"
GET_LOGIN_PASSWORD_TEXT = "«Получить логин и пароль» - нажимай!"
REDIRECT_TEXT = 'Вот и все! Теперь можно вернуться на сайт https://account.aipr.pro и авторизоваться!'

YOUR_LOGIN = 'Ваш логин: '
YOUR_PASSWORD = 'Ваш пароль: '
