import telebot

from config import MY_TOKEN
import keyboards as MY_KEYBOARD
import consts as MY_CONSTS
import functions as MY_FUNCTIONS

bot = telebot.TeleBot(MY_TOKEN.TOKEN, parse_mode="MARKDOWN")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, MY_CONSTS.MSG_WELLCOME_TEXT, reply_markup=MY_KEYBOARD.wellcome_keyboard)

@bot.message_handler(content_types=['text'])
def messageAnswer(message):
	if message.text == MY_CONSTS.GET_LOGIN_PASSWORD_TEXT:
		answer = MY_FUNCTIONS.getLoginPassword(message.chat.id)
		bot.reply_to(message, answer)
	elif message.text == MY_CONSTS.GET_ENTER_LINK:
		answer = MY_FUNCTIONS.getMagicLink(message.chat.id)
		bot.reply_to(message, answer)
	else:
		bot.reply_to(message, MY_CONSTS.MSG_WELLCOME_TEXT, reply_markup=MY_KEYBOARD.wellcome_keyboard)

bot.infinity_polling()
