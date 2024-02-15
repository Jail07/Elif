import telebot
import sqlite3
from telebot import types
import datetime

from database import create_table, create_conn
from database import staff, projects, execute_query
from Elif_Bot.database import failed_project, completed_project, approved_project, order
from admin.configE import Bot_MAIN

bot = telebot.TeleBot(Bot_MAIN)
user_data_dict = {}
# completed_order = {}
# failing_order = {}
user_message_stack = {}


'#________________________________________________________________#'

def delete_last_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка в удалении сообщении: {e}")

def schedule_notifications(message, deadline):
    current_time = datetime.date.today()
    time_difference = deadline - current_time
    days_until_deadline = time_difference.days

    if days_until_deadline == 3:
        bot.send_message(message.chat.id, "У вас осталось 3 дня до дедлайна!")
    elif days_until_deadline == 0:
        bot.send_message(message.chat.id, "Дедлайн сегодня!")
    else:
        project_id = proj_id(message, deadline)
        failed_project(project_id)


def proj_id(message, deadline):
    connection = sqlite3.connect('../Elif_Bot/db.sql')
    user_id = message.user_id
    cursor = connection.cursor()
    cursor.execute('SELECT staff_id FROM staff WHERE staff_id_tg = ?', (user_id,))
    staff_id = cursor.fetchone()
    cursor.execute('SELECT project_id FROM project_staff WHERE staff_id = ?, deadline=?', (staff_id, deadline,))
    project_id = cursor.fetchone()
    return project_id


@bot.message_handler(commands=['start'])
def staff_account(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        user_message_stack[chat_id] = []
        user_message_stack[chat_id].append(bot.send_message(chat_id, "Добро пожаловать!"))

        connection = sqlite3.connect('../Elif_Bot/db.sql')
        cursor = connection.cursor()
        cursor.execute('SELECT staff_id_tg FROM staff')
        staff_id = cursor.fetchone()
        if staff_id is not None:
            user_message_stack[chat_id].append(bot.send_message(chat_id, "Выберите опцию:"))
        if user_id in staff_id:
            staff_account_options(message)
            bot.delete_message(chat_id, user_message_stack[chat_id].pop().message_id)
        else:
            bot.send_message(chat_id, "Добро пожаловать! Увы, но вы не являетесь сотрудником, так что идите к админу.")
        cursor.execute('SELECT project_id FROM staff WHERE staff_id_tg = ?', (staff_id,))
        project_id = cursor.fetchone()
        cursor.execute('SELECT deadline FROM projects WHERE project_id = ?', (project_id,))
        deadline = cursor.fetchone()
        for i in deadline:
            schedule_notifications(message, i)
    except:
        bot.send_message(message.chat.id, 'Извините, но в данный момент Бот на ремонте')
    finally:
        cursor.close()
        connection.close()


def staff_account_options(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Обо мне↗️", callback_data='my_info'))
    markup.add(types.InlineKeyboardButton("Мой заказ⏎", callback_data='my_order'))
    markup.add(types.InlineKeyboardButton("Состав сотрудников⏎", callback_data='staff_list'))
    markup.add(types.InlineKeyboardButton("Отделы под заказы⏎", callback_data='departments'))
    markup.add(types.InlineKeyboardButton("Elif инстаграмм группы⏎", callback_data='site'))
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
    markup.add(types.InlineKeyboardButton("Elif Education",
                                          url='https://www.instagram.com/elif_education/?igsh=dTN1cXBsY21zNDF2'))
    markup.add(types.InlineKeyboardButton("Elif Commerce",
                                          url='https://www.instagram.com/elif_commerce/?igsh=MWt0YWt6Ymw2dmN4YQ%3D%3D'))
    markup.add(types.InlineKeyboardButton("Elif Digital",
                                          url='https://www.instagram.com/elif_digital/?igsh=c2t5MThoNWhkZDA2'))
    markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
    bot.send_message(chat_id, '卐 Список инстаграмм сайтов:', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'departments')
def departments(callback):
    chat_id = callback.message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📲Заказы для Digital", callback_data='show_orders_Digital'))
    markup.add(types.InlineKeyboardButton("📲Заказы для Education", callback_data='show_orders_Education'))
    markup.add(types.InlineKeyboardButton("📲Заказы для Commerce", callback_data='show_orders_Commerce'))
    markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
    bot.send_message(chat_id, 'Просмотр заказов:', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'my_info')
def my_info(callback):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    connection = sqlite3.connect('../Elif_Bot/db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM staff WHERE staff_id_tg = ?', (user_id,))
    user = cursor.fetchone()
    print(user)
    project = user[4]

    if user[4] is None:
        project = "У вас пока нет проектов"

    if user:
        info_message = (f"Ваши данные:\nИмя: {user[1]}"
                        f"\nID сотрудника: {user[0]}"
                        f"\nСпециальность: {user[3]}"
                        f"\nЗаконченные заказ(ы): {user[5]}"
                        f"\nПроваленные заказ(ы): {user[6]}"
                        f"\nЗаказ: {project}"
                        f"\nСтатус: Staff")
        bot.send_message(chat_id, info_message)
    else:
        bot.send_message(chat_id, "Информация о вас не найдена. Обратитесь к админу")

    cursor.close()
    connection.close()

# @bot.callback_query_handler(func=lambda callback: callback.data == 'my_order')
# def list_my_order(callback):
#     chat_id = callback.message.chat.id
#     user_id = callback.message.from_user.id
#     connection = sqlite3.connect('../Elif_Bot/db.sql')
#     cursor = connection.cursor()
#     cursor.execute('SELECT project_id FROM staff WHERE staff_id_tg = ?', (user_id,))
#     project_id = cursor.fetchone()
#     print(project_id)
#     cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
#     order = cursor.fetchall()
#     print(order)
#     markup = types.InlineKeyboardMarkup()
#     if order is not None:
#         markup.add(types.InlineKeyboardButton(f"Ваш заказ {order[1]}", callback_data=f'your_order_{order[0]}'))
#         markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
#
#         bot.send_message(chat_id, f"📱Ваш лист заказов:", reply_markup=markup)
#     else:
#         markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
#         bot.send_message(chat_id, f"📱У вас нет заказов:", reply_markup=markup)
#     cursor.close()
#     connection.close()


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('my_order'))
def my_order(callback):
    chat_id = callback.message.chat.id
    connection = sqlite3.connect('../Elif_Bot/db.sql')
    user_id = callback.from_user.id
    cursor = connection.cursor()
    cursor.execute('SELECT project_id FROM staff WHERE staff_id_tg = ?', (user_id,))
    project_id = cursor.fetchone()[0]
    cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
    project = cursor.fetchone()


    if project:
        print(project[6])
        if str(project[6]) == 'В ожидании' or str(project[6]) == "В процессе":
            project_info = (f"Информация о вашем заказе:\n"
                            f"Номер заказа: {project[0]}\n"
                            f"Название заказа: {project[1]}\n"
                            f"Отдел: {project[4]}\n"
                            f"Описание заказа: {project[2]}\n"
                            f"Дедлайн: {project[7]}\n"
                            f"Статус заказа: {project[6]}")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Закончить заказ", callback_data=f'finish_order:{project[0]}'))
            markup.add(types.InlineKeyboardButton("Отказаться от заказа", callback_data=f'fail_order:{project[0]}'))
            markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
            bot.send_message(chat_id, project_info, reply_markup=markup)
        elif str(project[6]) == 'Провален':
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
            bot.send_message(chat_id, "Вы провалили заказ", reply_markup=markup)

        elif str(project[6]) == 'Завершен':
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
            bot.send_message(chat_id, "Вы завершили проект", reply_markup=markup)
        else:
            pass
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
        bot.send_message(chat_id, "У вас нет заказа.", reply_markup=markup)



@bot.callback_query_handler(func=lambda callback: callback.data.startswith('finish_order:'))
def finish_the_order(callback):
    delete_last_message(callback.message.chat.id, callback.message.message_id)
    chat_id = callback.message.chat.id
    print(callback.data)
    order_id = int(callback.data.split(':')[1])
    print(order_id)
    completed_project(order_id)
    my_order(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('fail_order:'))
def fail_order(callback):
    delete_last_message(callback.message.chat.id, callback.message.message_id)
    chat_id = callback.message.chat.id
    order_id = int(callback.data.split(':')[1])
    failed_project(order_id)
    my_order(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('show_orders_'))
def show_orders(callback):
    chat_id = callback.message.chat.id
    group = callback.data.split('_')[-1]
    connection = sqlite3.connect('../Elif_Bot/db.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM projects WHERE "group" = ?', (group,))
    projects = cursor.fetchall()
    cursor.close()
    connection.close()

    if projects:
        for project in projects:
            project_info = (f"Информация о заказе:\n"
                            f"Номер заказа: {project[0]}\n"
                            f"Название заказа: {project[1]}\n"
                            f"Отдел: {project[4]}\n"
                            f"Описание заказа: {project[2]}\n"
                            f"Дедлайн: {project[7]}\n"
                            f"Статус заказа: {project[6]}")
            bot.send_message(chat_id, project_info)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
        bot.send_message(chat_id, f"Нет заказов для группы {group}", reply_markup=markup)

#
# @bot.callback_query_handler(func=lambda callback: callback.data.startswith('show_orders'))
# def show_orders_callback(callback):
#     chat_id = callback.message.chat.id
#     group = callback.data.split('_')[-1]
#     show_order_info(chat_id, group)
#
#
# def show_order_info(chat_id, group):
#     connection = sqlite3.connect('../Elif_Bot/db.sql')
#     cursor = connection.cursor()
#
#     cursor.execute('SELECT * FROM projects WHERE "group" = ?', (group,))
#     orders = cursor.fetchall()
#     cursor.close()
#     connection.close()
#
#     if orders:
#         for order in orders:
#             bot.send_message(chat_id, f"Заказ: {order[1]}:\n"
#                                       f"ID заказчика: {order[0]}\n"
#                                       f"Описание: {order[2]}\n"
#                                       f"Статус: {order[6]}")
#     else:
#         markup = types.InlineKeyboardMarkup()
#         markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
#         bot.send_message(chat_id, f"Нет заказов|заказа для группы {group}", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'staff_list')
def show_staff_list(callback):
    chat_id = callback.message.chat.id
    connection = sqlite3.connect('../Elif_Bot/db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT full_name, project_id FROM staff')
    users = cursor.fetchall()
    markup = types.InlineKeyboardMarkup()



    if users:
        for user in users:
            markup.add(types.InlineKeyboardButton(f"🙍 Сотрудник {user[0]}", callback_data=f'staff_info_{user[0]}'))
        markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
        cursor.close()
        connection.close()
        bot.send_message(chat_id, "Состав сотрудников (🙍):", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
        bot.send_message(chat_id, f"Состав сотрудников|сотрудника (🙍)", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('staff_info_'))
def show_staff_info_callback(callback):
    user_name = callback.data.split('_')[-1]
    show_staff_info(callback.message.chat.id, user_name)


def show_staff_info(chat_id, user_name):
    connection = sqlite3.connect('../Elif_Bot/db.sql')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM staff WHERE full_name = ?', (user_name,))
    user = cursor.fetchone()

    project = user[4]

    if user[4] is None:
        project = "У вас пока нет проектов"
    if user:
        info_message = (f"Информация о сотруднике:\nИмя: {user[1]}"
                        f"\nID сотрудника: {user[0]}"
                        f"\nСпециальность: {user[3]}"
                        f"\nЗаконченные заказ(ы): {user[5]}"
                        f"\nПроваленные заказ(ы): {user[6]}"
                        f"\nЗаказ: {project}"
                        f"\nСтатус: Staff")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
        bot.send_message(chat_id, info_message, reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙Назад", callback_data='back'))
        bot.send_message(chat_id, f"Нету информации о сотруднике (🙍)", reply_markup=markup)

    cursor.close()
    connection.close()


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