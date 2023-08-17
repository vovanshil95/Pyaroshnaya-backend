import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get('BOT_TOKEN')

MSG_WELLCOME_TEXT = "Привет! Выберите действие:"
GET_LOGIN_PASSWORD_TEXT = "Получить логин/пароль"

YOUR_LOGIN = 'Ваш логин: '
YOUR_PASSWORD = 'Ваш пароль: '
