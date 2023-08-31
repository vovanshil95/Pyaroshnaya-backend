import telebot
import os
import sys

sys.path.append(os.getcwd())

from bot.config_ import TOKEN
import keyboards as KEYBOARD
import bot.config_ as CONSTS
from functions import get_login_password

bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, CONSTS.MSG_WELLCOME_TEXT, reply_markup=KEYBOARD.wellcome_keyboard)

@bot.message_handler(content_types=['text'])
def messageAnswer(message):
	if message.text == CONSTS.GET_LOGIN_PASSWORD_TEXT:
		answer = get_login_password(message.chat.id)
		bot.reply_to(message, f'{answer}\n{CONSTS.REDIRECT_TEXT}')
	else:
		bot.reply_to(message, CONSTS.MSG_WELLCOME_TEXT, reply_markup=KEYBOARD.wellcome_keyboard)

bot.infinity_polling()
