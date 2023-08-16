import telebot

from config import MY_TOKEN
import my_keyboards as MY_KEYBOARD
import my_consts as MY_CONSTS
import my_functions as MY_FUNCTIONS

bot = telebot.TeleBot(MY_TOKEN.TOKEN, parse_mode="MARKDOWN") # You can set parse_mode by default. HTML or MARKDOWN

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
