import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton as IKB
import database
import os
from dotenv import load_dotenv
load_dotenv()
bot = telebot.TeleBot(os.getenv("tg_bot_token"))

def create_menu():
    """
    Create the menu
    :return kb:
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Криптовалюта")
    kb.row("Подписки")
    kb.row("Настройки")
    return kb

def ask_register_new_user(msg):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row("да", "нет")
    bot.send_message(msg.chat.id, "Вы ещё не зарегистрированы! Желаете пройти регистрацию?", reply_markup=kb, reply_to_message_id=msg.id)
    bot.register_next_step_handler(msg, register_new_user)

def register_new_user(msg):
    if msg.text.lower().replace(" ", "") == "да":
        database.register_new_user(msg.chat.id, "",True)
        bot.send_message(msg.chat.id, "Вы зарегистрированы!", reply_markup=create_menu())
    else:
        choice_page(msg)

def choice_page(msg):
    bot.send_message(msg.chat.id, "Выберите раздел:", reply_markup=create_menu())

@bot.message_handler(content_types=["text"])
def handler_message(msg):
    func = {
        "Меню" : choice_page,
        "Криптовалюта" : ...,
        "Подписки": ...,
        "Настройки": ...,

    }
    if database.check_new_user(msg.chat.id):
        ask_register_new_user(msg)
    else:
        choice_page(msg)

bot.infinity_polling()
