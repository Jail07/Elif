import telebot
import sqlite3
from telebot import types

from Elif_Bot.database import create_table, create_conn
from Elif_Bot.database import staff, projects, project_staff, execute_query
from admin.configE import Bot_MAIN, STAFF

bot = telebot.TeleBot(Bot_MAIN)
user_data_dict = {}
completed_order = {}
failing_order = {}
user_message_stack = {}


'#________________________________________________________________#'


conn = create_conn('db.sql')
execute_query(conn, staff)
execute_query(conn, projects)
execute_query(conn, project_staff)


if 'tgbot/../admin/db.sql' == None:
    execute_query(conn, create_table)


@bot.message_handler(commands=['start'])
def staff_account(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    user_message_stack[chat_id] = []
    user_message_stack[chat_id].append(bot.send_message(chat_id, "Добро пожаловать!"))
    user_message_stack[chat_id].append(bot.send_message(chat_id, "Выберите опцию:"))

    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM staff WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user or user_id in STAFF:
        staff_account_options(message)
        bot.delete_message(chat_id, user_message_stack[chat_id].pop().message_id)
    else:
        bot.send_message(chat_id, "Добро пожаловать! Увы, но вы не являетесь сотрудником, так что идите на.")


def staff_account_options(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Обо мне", callback_data='my_info'))
    markup.add(types.InlineKeyboardButton("Мой заказ", callback_data='my_order'))
    markup.add(types.InlineKeyboardButton("Состав сотрудников", callback_data='staff_list'))
    markup.add(types.InlineKeyboardButton("Отделы под заказы", callback_data='departments'))
    markup.add(types.InlineKeyboardButton("Elif инстаграмм группы", callback_data='site'))
    bot.send_sticker(chat_id, 'CAACAgIAAxkBAAELUpdlwQHvUbQ9ErskmtpXzxCQm5ZLzwACNgEAArd76yBQQ9oMJi0mBjQE')
    bot.send_message(chat_id, 'Выберите опцию:', reply_markup=markup)


def clear_message_stack(chat_id):
    if chat_id in user_message_stack:
        for message in user_message_stack[chat_id]:
            bot.delete_message(chat_id, message.message_id)
        user_message_stack[chat_id] = []


def send_new_message(chat_id, text, reply_markup=None):
    clear_message_stack(chat_id)
    if chat_id in user_message_stack and user_message_stack[chat_id]:
        bot.delete_message(chat_id, user_message_stack[chat_id].pop().message_id)
    message = bot.send_message(chat_id, text, reply_markup=reply_markup)
    if chat_id not in user_message_stack:
        user_message_stack[chat_id] = []
    user_message_stack[chat_id].append(message)


@bot.callback_query_handler(func=lambda callback: callback.data == 'site')
def site(callback):
    chat_id = callback.message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Elif Education",url='https://www.instagram.com/elif_education/?igsh=dTN1cXBsY21zNDF2'))
    markup.add(types.InlineKeyboardButton("Elif Commerce", url='https://www.instagram.com/elif_commerce/?igsh=MWt0YWt6Ymw2dmN4YQ%3D%3D'))
    markup.add(types.InlineKeyboardButton("Elif Digital", url='https://www.instagram.com/elif_digital/?igsh=c2t5MThoNWhkZDA2'))
    markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
    bot.send_message(chat_id, 'Список инстаграмм сайтов:', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'departments')
def departments(callback):
    chat_id = callback.message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Заказы для Digitals", callback_data='show_orders'))
    markup.add(types.InlineKeyboardButton("Заказы для Education", callback_data='show_orders'))
    markup.add(types.InlineKeyboardButton("Заказы для Commerce", callback_data='show_orders'))
    markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
    bot.send_message(chat_id, 'Просмотр заказов:', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'my_info')
def my_info(callback):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM staff WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user:
        info_message = (f"Информация:\nName: {user[1]}\n"
                        f"Описание: {user[2]}\n"  
                        f"Статус: {'Staff'}")
        bot.send_message(chat_id, info_message)
    else:
        bot.send_message(chat_id, "Информация о вас не найдена. Обратитесь к админу")


@bot.callback_query_handler(func=lambda callback: callback.data == 'my_order')
def list_my_order(callback):
    chat_id = callback.message.chat.id
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM project_staff WHERE staff_id = ?', (chat_id,))
    orders = cursor.fetchall()
    markup = types.InlineKeyboardMarkup()
    if orders:
        for i, order in enumerate(orders, start=1):
            markup.add(types.InlineKeyboardButton(f"Ваш заказ {i}", callback_data=f'your_order_{order[0]}'))
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        cursor.close()
        connection.close()
        bot.send_message(chat_id, f"Ваш лист заказов:", reply_markup=markup)
    else:
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        bot.send_message(chat_id, f"У вас нет заказов:", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('your_order'))
def my_order(callback):
    chat_id = callback.message.chat.id
    order_id = int(callback.data.split('_')[-1])
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM project_staff WHERE staff_id = ? AND project_id = ?', (chat_id, order_id))
    order = cursor.fetchone()

    if order:
        order_info = (f"Информация о вашем заказе:\n"
                      f"Номер заказа: {order[0]}\n"
                      f"ID заказа: {order[1]}\n"
                      f"Описание заказа: {order[2]}\n"
                      f"Статус заказа: {order[3]}")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Закончить заказ", callback_data='finish_order'))
        markup.add(types.InlineKeyboardButton("Отказаться от заказа", callback_data='fail_order'))
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        bot.send_message(chat_id, order_info, reply_markup=markup)
    else:
        bot.send_message(chat_id, "У вас нет заказа.")


@bot.callback_query_handler(func=lambda callback: callback.data == 'finish_order')
def finish_the_order(callback):
    chat_id = callback.message.chat.id
    order_id = int(callback.message.text.split('\n')[1].split(': ')[1])  # Получаем ID заказа из сообщения
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()
    cursor.execute('UPDATE projects SET status = "Completed" WHERE id = ?', (order_id,))
    connection.commit()
    cursor.close()
    connection.close()

    if chat_id in failing_order:
        failing_order.pop(chat_id)

    completed_order[chat_id] = order_id

    bot.send_message(chat_id, "Вы успешно завершили проект.")
    list_my_order(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'fail_order')
def fail_order(callback):
    chat_id = callback.message.chat.id
    order_id = int(callback.message.text.split('\n')[1].split(': ')[1])
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()
    cursor.execute('UPDATE projects SET status = "Failed" WHERE id = ?', (order_id,))
    connection.commit()
    cursor.close()
    connection.close()

    if chat_id in completed_order:
        completed_order.pop(chat_id)

    failing_order[chat_id] = order_id

    bot.send_message(chat_id, "Вы отказались от проекта.")
    list_my_order(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('show_orders'))
def show_orders(callback):
    chat_id = callback.message.chat.id
    group = callback.data.split('_')[-1]
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM projects ')
    # cursor.execute('SELECT * FROM projects WHERE "group" = ?', (group,))

    orders = cursor.fetchall()
    cursor.close()
    connection.close()

    if orders:
        for order in orders:
            bot.send_message(chat_id, f"Заказ: {order[1]}:\n"
                                      f"ID заказчика: {order[1]}\n"
                                      f"Описание: {order[2]}\n"
                                      f"Статус: {order[3]}")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        bot.send_message(chat_id, f"Нет заказов для группы {group}", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('order'))
def show_orders_callback(callback):
    chat_id = callback.message.chat.id
    group = callback.data.split('_')[-1]
    show_order_info(chat_id, group)


def show_order_info(chat_id, group):
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM projects ')
    # cursor.execute('SELECT * FROM projects WHERE "group" = ?', (group,))

    orders = cursor.fetchall()
    cursor.close()
    connection.close()

    if orders:
        for order in orders:
            bot.send_message(chat_id, f"Заказ: {order[1]}:\n"
                                      f"ID заказчика: {order[1]}\n"
                                      f"Описание: {order[2]}\n"
                                      f"Статус: {order[3]}")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        bot.send_message(chat_id, f"Нет заказов для группы {group}", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'staff_list')
def show_staff_list(callback):
    chat_id = callback.message.chat.id
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT full_name, project_id FROM staff')
    users = cursor.fetchall()
    markup = types.InlineKeyboardMarkup()

    if users:
        for user in users:
            markup.add(types.InlineKeyboardButton(f"Сотрудник {user[0]}", callback_data=f'staff_info_{user[0]}'))
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        cursor.close()
        connection.close()
        bot.send_message(chat_id, "Состав сотрудников:", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        bot.send_message(chat_id, f"Нету сотрудников", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('staff_info'))
def show_staff_info_callback(callback):
    user_id = int(callback.data.split('_')[-1])
    show_staff_info(callback.message.chat.id, user_id)


def show_staff_info(chat_id, user_id):
    connection = sqlite3.connect('db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM staff WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        info_message = f"Информация об этом сотруднике:\nName: {user[1]}"
        bot.send_message(chat_id, info_message)


@bot.callback_query_handler(func=lambda callback: callback.data == 'back')
def handle_back(callback):
    chat_id = callback.message.chat.id
    clear_message_stack(chat_id)

    current_message_id = callback.message.message_id

    bot.delete_message(chat_id, current_message_id)

    if chat_id in user_message_stack and user_message_stack[chat_id]:
        bot.delete_message(chat_id, user_message_stack[chat_id][0].message_id)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    message = callback.message
    if callback.data == 'back':
        staff_account(message)


bot.polling(none_stop=True)