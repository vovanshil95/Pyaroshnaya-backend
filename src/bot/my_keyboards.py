# import telebot
from telebot import types
import my_consts as CONST

# markup = types.InlineKeyboardMarkup()
wellcome_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=False, one_time_keyboard=True)
# markup = types.ReplyKeyboardMarkup()
# itembtna = types.InlineKeyboardButton(text='/getLogin - Получить логин/пароль для личного кабинета', callback_data='v1')
# itembtnv = types.InlineKeyboardButton(text='/getLink - Получить ссылку для входа в личный кабинет', callback_data='v2')
itemBtn1 = types.InlineKeyboardButton(text=CONST.GET_LOGIN_PASSWORD_TEXT, callback_data='v1', row_width=1)
itemBtn2 = types.InlineKeyboardButton(text=CONST.GET_ENTER_LINK, callback_data='v2', row_width=1)
wellcome_keyboard.add(itemBtn1, itemBtn2)