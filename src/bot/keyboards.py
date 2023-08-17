from telebot import types
import bot.config as CONSTS

wellcome_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=False, one_time_keyboard=True)
itemBtn1 = types.InlineKeyboardButton(text=CONSTS.GET_LOGIN_PASSWORD_TEXT, callback_data='v1', row_width=1)
itemBtn2 = types.InlineKeyboardButton(text=CONSTS.GET_ENTER_LINK, callback_data='v2', row_width=1)
wellcome_keyboard.add(itemBtn1, itemBtn2)
