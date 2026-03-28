import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton as IKB
import database
import os
from dotenv import load_dotenv
import parser

coin_parser = parser.Parser("https://coinmarketcap.com/all/views/all/")
coin_parser.get_all_coins()
coin_parser.load_to_database()
load_dotenv()
bot = telebot.TeleBot(os.getenv("tg_bot_token"))
users_date = {}

def create_keyboard_menu():
    """
    Create the menu
    :return kb:
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Криптовалюта")
    kb.row("Подписки")
    kb.row("Настройки")
    return kb

def create_settings_menu(alert : bool = True, percent : int = "error"):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(f"Поменять процент ({percent}%)")
    if alert:
        text = "Отключить рассылку"
    else:
        text = "Подключить рассылку"
    kb.row(text)
    kb.row("Меню")
    return kb


def ask_register_new_user(msg):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row("да", "нет")
    bot.send_message(msg.chat.id, "Вы ещё не зарегистрированы! Желаете пройти регистрацию?", reply_markup=kb, reply_to_message_id=msg.id)
    bot.register_next_step_handler(msg, ask_percent)

def ask_percent(msg):
    if msg.text.lower().replace(" ", "") == "да":
        bot.send_message(msg.chat.id, "Введите % при котором вам будет приходить оповещение. (от 5 до 1000)", reply_to_message_id=msg.id)
        bot.register_next_step_handler(msg, register_new_user)

def register_new_user(msg):
    percent = int(msg.text)
    if 5 <= percent <= 1000:
        database.register_new_user(msg.chat.id, "",True, percent)
        bot.send_message(msg.chat.id, "Вы зарегистрированы!", reply_markup=create_keyboard_menu())
    else:
        choice_page(msg)

def choice_page(msg):
    bot.send_message(msg.chat.id, "Раздел 'Меню':", reply_markup=create_keyboard_menu())

def show_all_coins(msg):
    all_coins = database.get_all_coins()
    all_user_coins = database.get_coins_sub_user(msg.chat.id)
    kb = InlineKeyboardMarkup()
    for coin in all_coins:
        price = float(coin.price)
        # Для стабильных монет (USDT, USDC) - 4 знака
        # Для остальных - 2 знака
        if coin.name in ['USDT', 'USDC', 'DAI']:
            price_display = f"{price:.4f}"
        else:
            price_display = f"{price:,.2f}"
        if coin.id in map(int, all_user_coins.target.split("_")):
            text = f"✅ {coin.name} | {price_display}$"
        else:
            text = f"❌ {coin.name} | {price_display}$"
        kb.row(IKB(text, callback_data=f"sub_{coin.id}"))
    bot.send_message(msg.chat.id, f"Раздел: '{msg.text}'", reply_markup=kb)

def subscriptions(msg):
    all_user_coins_sub = database.get_coins_sub_user(msg.chat.id)
    all_user_coins = database.get_coin_from_user(all_user_coins_sub.target.split("_"))
    kb = InlineKeyboardMarkup()
    kb = InlineKeyboardMarkup()
    for coin in all_user_coins:
        price = float(coin.price)
        # Для стабильных монет (USDT, USDC) - 4 знака
        # Для остальных - 2 знака
        if coin.name in ['USDT', 'USDC', 'DAI']:
            price_display = f"{price:.4f}"
        else:
            price_display = f"{price:,.2f}"
        kb.row(IKB(text = f"✅ {coin.name} | {price_display}$", callback_data=f"unsub_{coin.id}"))
    bot.send_message(msg.chat.id, f"Раздел: '{msg.text}'\n"
                                  f"Чтобы отписаться от валюты - нажмите на кнопку ниже", reply_markup=kb)

def settings(msg):
    user = database.get_user_info(msg.chat.id)
    bot.send_message(msg.chat.id, f"Раздел '{msg.text}'",
                     reply_markup=create_settings_menu(user.alerts, user.percent))

@bot.message_handler(content_types=["text"])
def handler_message(msg):
    func = {
        "Меню" : choice_page,
        "Криптовалюта" : show_all_coins,
        "Подписки": subscriptions,
        "Настройки": settings,
        "Поменять процент" : ...,
        "Отключить рассылку" : ...,
        "Подулючить рассылку" : ...,

    }
    if database.check_new_user(msg.chat.id):
        ask_register_new_user(msg)
    if not(database.check_new_user(msg.chat.id)) and msg.text in func.keys():
        func[msg.text](msg)
    else:
        choice_page(msg)


bot.infinity_polling()
