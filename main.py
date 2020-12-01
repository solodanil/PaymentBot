import telebot
from telebot.types import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
import os
from config import path

token = '1446058419:AAFxzLbOKsV1PPl7eT2x6nGZsnFKrLSI-68'
provider_token = '381764678:TEST:20845'  # @BotFather -> Bot Settings -> Payments
bot = telebot.TeleBot(token)

prices = [LabeledPrice(label='Архив фотографий', amount=9900)]
users = dict()

main_kb = InlineKeyboardMarkup()
main_kb.add(InlineKeyboardButton(text='Последние фотографии', callback_data='recent'))
main_kb.add(InlineKeyboardButton(text='Темы', callback_data='themes'),
            InlineKeyboardButton(text='Почта для связи', callback_data='email'))


def get_themes_keyboard():
    keyboard = InlineKeyboardMarkup()
    for theme in os.listdir(path):
        if theme not in ('.idea', 'main.py', 'config.py', '__pycache__'):
            keyboard.add(InlineKeyboardButton(text=theme, callback_data=theme))
    return keyboard


def get_subthemes_keyboard(theme):
    keyboard = InlineKeyboardMarkup()
    for theme in os.listdir(f'{path}/{theme}'):
        if theme not in ('.idea', 'main.py'):
            keyboard.add(InlineKeyboardButton(text=theme, callback_data=theme))
    return keyboard


def send_recents(chat_id):
    res = []
    for theme in os.listdir(path):
        if theme not in ('.idea', 'main.py', 'config.py', '__pycache__'):
            for subtheme in os.listdir(f'{path}/{theme}'):
                res.append(theme + '/' + subtheme)
    res.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    for theme in res[:2]:
        command_pay(chat_id, theme)


@bot.message_handler(commands=['start'])
def command_start(message):
    bot.send_message(message.chat.id, '''В меню вы найдете удобные разделы для поиска по магазну \n
Последние фоторгафии — 9 последних архивов.
Тема — темы архивов фотографий, например «Лето», «Осень», «Море»…
Почта для связи — на почту можете написать любой вопрос или в случае неполадок.''',
                     reply_markup=main_kb)


@bot.message_handler(commands=['buy'])
def command_pay(chat_id, user):
    with open(user + '/description.txt', 'r',  encoding='windows-1251') as f:
        desc = '\n'.join(f.readlines())
    bot.send_invoice(chat_id, title=user,
                     description=desc,
                     provider_token=provider_token,
                     currency='rub',
                     photo_url='http://erkelzaar.tsudao.com/models/perrotta/TIME_MACHINE.jpg',    # path + '/' + user + '/cover.png',
                     photo_height=512,  # !=0/None or picture won't be shown
                     photo_width=512,
                     photo_size=512,
                     is_flexible=False,  # True If you need to set up Shipping Fee
                     prices=prices,
                     start_parameter='1234567890',
                     invoice_payload=user)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Произошла ошибка, попробуйте еще раз или "
                                                "напишите на почту")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id, 'Спасибо за покупку',
                     parse_mode='Markdown')
    print(message.successful_payment.invoice_payload)
    for file_name in os.listdir(path + '/' + message.successful_payment.invoice_payload):
        if file_name not in ('description.txt'):
            bot.send_document(message.chat.id,
                              open(message.successful_payment.invoice_payload + '/' + file_name,
                                   'rb'))
    command_start(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'themes':
        try:
            bot.send_message(call.message.chat.id, 'Выбор темы', reply_markup=get_themes_keyboard())
        except Exception as ex:
            bot.send_message(300208456, f'{call.message.chat.id} {call.from_user}: {type(ex)} {ex}')
    elif call.data == 'recent':
        try:
            send_recents(call.message.chat.id)
        except Exception as ex:
            bot.send_message(300208456, f'{call.message.chat.id} {call.from_user}: {type(ex)} {ex}')
    elif call.data in os.listdir(path):
        try:
            bot.send_message(call.message.chat.id, 'Выбор подтемы',
                             reply_markup=get_subthemes_keyboard(call.data))
            users[call.from_user.id] = call.data
        except Exception as ex:
            bot.send_message(300208456, f'{call.message.chat.id} {call.from_user}: {type(ex)} {ex}')
    else:
        if call.from_user.id in users:
            try:
                users[call.from_user.id] = f'{users[call.from_user.id]}/{call.data}'
                command_pay(call.message.chat.id, users[call.from_user.id])
            except Exception as ex:
                bot.send_message(300208456,
                                 f'{call.message.chat.id} @{call.from_user.username}: {type(ex)} {ex}')


if __name__ == '__main__':
    bot.skip_pending = True
    bot.polling(none_stop=True, interval=0)
