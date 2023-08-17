import telebot

from bot.config import TOKEN
import keyboards as KEYBOARD
import bot.config as CONSTS
from functions import get_login_password, getMagicLink

bot = telebot.TeleBot(TOKEN, parse_mode="MARKDOWN")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, CONSTS.MSG_WELLCOME_TEXT, reply_markup=KEYBOARD.wellcome_keyboard)

@bot.message_handler(content_types=['text'])
def messageAnswer(message):
	if message.text == CONSTS.GET_LOGIN_PASSWORD_TEXT:
		answer = get_login_password(message.chat.id)
		bot.reply_to(message, answer)
	elif message.text == CONSTS.GET_ENTER_LINK:
		answer = getMagicLink(message.chat.id)
		bot.reply_to(message, answer)
	else:
		bot.reply_to(message, CONSTS.MSG_WELLCOME_TEXT, reply_markup=KEYBOARD.wellcome_keyboard)

bot.infinity_polling()
