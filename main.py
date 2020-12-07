import telebot
from telebot.types import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, ReplyKeyboardRemove
import os
import shutil
from config import path, admins

token = '1446058419:AAEREFM72wBh-EtNSLNaHIejmoq2jXtPKHY'
provider_token = '390540012:LIVE:13591'  # @BotFather -> Bot Settings -> Payments
bot = telebot.TeleBot(token)

prices = [LabeledPrice(label='Архив фотографий', amount=9900)]
users = dict()
admin_mode = 0
# 1 — Ввод названия новой темы тема
# 2 — Ввод названия новой подтемы
# 3 — Ввод описания новой подтемы
# 4 — Обложка
# 5 — Добавление фотографий

main_kb = InlineKeyboardMarkup()
main_kb.add(InlineKeyboardButton(text='Последние фотографии', callback_data='recent'))
main_kb.add(InlineKeyboardButton(text='Темы', callback_data='themes'))


done_kb = ReplyKeyboardMarkup(one_time_keyboard=True)
done_kb.row('Готово')


def get_themes_keyboard(is_admin):
    res = []
    keyboard = InlineKeyboardMarkup()
    for theme in os.listdir(path):
        if theme not in ('.idea', 'main.py', 'config.py', '__pycache__', 'README.md', '.git'):
            res.append(theme)
    res.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    for theme in res:
        keyboard.add(InlineKeyboardButton(text=theme, callback_data=theme))
    if is_admin:
        keyboard.add(InlineKeyboardButton(text='➕Новая тема', callback_data=f'n_theme'))
    return keyboard


def get_subthemes_keyboard(theme, is_admin):
    res = []
    keyboard = InlineKeyboardMarkup()
    for subtheme in os.listdir(f'{path}/{theme}'):
        if subtheme not in ('.idea', 'main.py'):
            res.append(subtheme)
    res.sort(key=lambda x: os.path.getmtime(f'{theme}/{x}/cover.jpg'), reverse=True)
    for theme in res:
        keyboard.add(InlineKeyboardButton(text=theme, callback_data=theme))
    if is_admin:
        keyboard.add(InlineKeyboardButton(text='➕Новая подтема', callback_data=f'n_subtheme'))
    return keyboard


def send_recents(chat_id):
    res = []
    for theme in os.listdir(path):
        if theme not in ('.idea', 'main.py', 'config.py', '__pycache__', 'README.md', '.git'):
            for subtheme in os.listdir(f'{path}/{theme}'):
                res.append(theme + '/' + subtheme)
    res.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    for theme in res[:5]:
        command_pay(chat_id, theme)


@bot.message_handler(commands=['start'])
def command_start(message):
    bot.send_message(message.chat.id, '''В меню вы найдете удобные разделы для поиска по магазну \n
Последние фоторгафии — 9 последних архивов.
Тема — темы архивов фотографий, например «Лето», «Осень», «Море»…
Почта для связи — на почту можете написать любой вопрос или в случае неполадок.''',
                     reply_markup=main_kb)


@bot.message_handler(commands=['buy'])
def command_pay(chat_id, user, is_admin=False):
    with open(path + user + '/description.txt', 'r', encoding='utf-8') as f:
        desc = '\n'.join(f.readlines())
    if is_admin:
        invoice_kb = InlineKeyboardMarkup()
        invoice_kb.add(InlineKeyboardButton(text='Удалить', callback_data=f'del{user}'))
    else:
        invoice_kb = None
    with open(path + user + '/cover.jpg', 'rb') as f:
        bot.send_photo(chat_id, f, reply_markup=invoice_kb)
    bot.send_invoice(chat_id, title=user,
                     description=desc,
                     provider_token=provider_token,
                     currency='rub',
                     # photo_url='ftp://ftp_tele:123@195.133.144.133/PaymentBot' \
                     #           '/Животные/Белки/IMG_8336.jpg',
                     # path + '/' + user + '/cover.png',
                     # photo_height=512,  # !=0/None or picture won't be shown
                     # photo_width=512,
                     # photo_size=512,
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
        if file_name not in ('description.txt', 'cover.jpg'):
            bot.send_document(message.chat.id,
                              open(path + message.successful_payment.invoice_payload + '/' + \
                                   file_name,
                                   'rb'))
    command_start(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global admin_mode
    if call.data == 'themes':
        try:
            bot.send_message(call.message.chat.id, 'Выбор темы',
                             reply_markup=get_themes_keyboard(call.message.chat.id in admins))
        except Exception as ex:
            bot.send_message(300208456, f'@{call.from_user.username}: {type(ex)} {ex.args}')
    elif call.data == 'recent':
        try:
            send_recents(call.message.chat.id)
        except Exception as ex:
            bot.send_message(300208456, f'@{call.from_user.username}: {type(ex)} {ex.args}')
    elif call.data == 'n_theme':
        admin_mode = 1
        bot.send_message(call.message.chat.id, 'Введите название темы')
    elif call.data == 'n_subtheme':
        admin_mode = 2
        bot.send_message(call.message.chat.id, 'Введите название подтемы')
    elif call.data.startswith('del'):
        shutil.rmtree(f'{path}/{call.data.replace("del", "")}')
        bot.send_message(call.message.chat.id, 'Архив удален')
    elif call.data in os.listdir(path):
        try:
            bot.send_message(call.message.chat.id, 'Выбор подтемы',
                             reply_markup=get_subthemes_keyboard(call.data, call.message.chat.id in admins))
            users[call.from_user.id] = call.data
        except Exception as ex:
            bot.send_message(300208456, f'@{call.from_user.username}: {type(ex)} {ex.args}')
    else:
        try:
            if call.from_user.id in users:
                users[call.from_user.id] = f'{users[call.from_user.id]}/{call.data}'
                command_pay(call.message.chat.id, users[call.from_user.id], call.message.chat.id in admins)
                users.pop(call.from_user.id)
        except Exception as ex:
            bot.send_message(300208456, f'@{call.from_user.username}: {type(ex)} {ex.args}')


@bot.message_handler(content_types=['text'])
def msg_handler(call):
    global admin_mode
    if call.from_user.id in admins:
        if admin_mode == 1:
            os.mkdir(call.text)
            admin_mode = 0
            bot.send_message(call.chat.id, 'Выбор подтемы',
                             reply_markup=get_subthemes_keyboard(call.text, True))
            users[call.from_user.id] = call.text
        elif admin_mode == 2:
            admin_mode = 3
            users[call.from_user.id] = f'{users[call.from_user.id]}/{call.text}'
            os.mkdir(users[call.from_user.id])
            bot.send_message(call.chat.id, 'Введите описание')
        elif admin_mode == 3:
            with open(f'{users[call.from_user.id]}/description.txt', 'w') as f:
                f.write(call.text)
            admin_mode = 4
            bot.send_message(call.chat.id, 'Отправьте обложку фотографией')
        if admin_mode == 6 and call.text == 'Готово':
            admin_mode = 0
            bot.send_message(call.chat.id, 'Новый архим добавлен!',
                             reply_markup=ReplyKeyboardRemove())
            command_start(call)
    else:
        print(call.from_user.id)
        for user_id in admins:
            bot.send_message(user_id, f'@{call.from_user.username}: {call.text}')


@bot.message_handler(content_types=['document'])
def photo_handler(call):
    global admin_mode
    print(call)
    file_id = call.document.file_id
    file_info = bot.get_file(file_id)
    if admin_mode == 5:
        file = bot.download_file(file_info.file_path)
        with open(users[call.from_user.id] + '/' + call.document.file_name, 'wb+') as f:
            f.write(file)
        admin_mode = 6


@bot.message_handler(content_types=['photo'])
def photo_handler(call):
    global admin_mode
    print(call)
    file_id = call.photo[-1].file_id
    file_info = bot.get_file(file_id)
    if admin_mode == 4:
        file = bot.download_file(file_info.file_path)
        with open(users[call.from_user.id] + '/cover.jpg', 'wb+') as f:
            f.write(file)
        admin_mode = 5
        bot.send_message(call.chat.id, 'Отправьте фотографии файлом', reply_markup=done_kb)


if __name__ == '__main__':
    bot.skip_pending = True
    bot.polling(none_stop=True, interval=0)
