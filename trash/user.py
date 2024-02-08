from datetime import datetime

import telebot
import sqlite3
from telebot import types
from admin.configE import STAFF
from database import create_table, add_stuff, delete_db
from database import temp_proj_db, users_db, stuff_db, admin_db, project_students, projects_list
from database import create_conn
from admin.configE import Bot_MAIN

# bot = telebot.TeleBot(Bot_MAIN)


def bot_token(bot_t):
    bot = bot_t
    return bot


# @bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Добавить заказ', callback_data='add_order')
    btn2 = types.InlineKeyboardButton(text='Удалить Заказ', callback_data='delete_order')
    btn3 = types.InlineKeyboardButton(text='Изменить Заказ', callback_data='change_order')
    btn4 = types.InlineKeyboardButton('Мои заказы', callback_data='my_orders')
    btn5 = types.InlineKeyboardButton(text='Контакты разработчиков', callback_data='krasavchiki_elif')
    btn6 = types.InlineKeyboardButton(text='Жалоба', callback_data='complaint_elif')
    markup.row(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAELUpdlwQHvUbQ9ErskmtpXzxCQm5ZLzwACNgEAArd76yBQQ9oMJi0mBjQE')
    bot.send_message(message.chat.id, 'Добро пожаловать в Elif! Выберите то что вас интересует', reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def add_order(callback):
    if callback.data == 'add_order':
        bot.send_message(callback.message.chat.id, 'Дайте название вашему проекту: ')
        bot.register_next_step_handler(callback.message, add_project_name)

    elif callback.data == 'krasavchiki_elif':
        bot.send_message(callback.message.chat.id, "\nНурмухаммед Абдуллаев: 8-800-3-555"
                                                   "\nАлымбек Что-тотамов: 12324245234")

    elif callback.data == 'my_orders':
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()

        user_id = callback.from_user.id
        user_projects = cur.fetchall()

        if user_projects:
            orders_message = "Ваши заказы:\n"
            for project_name in user_projects:
                orders_message += f"- {project_name[0]}\n"

            bot.send_message(callback.message.chat.id, orders_message)
        else:
            bot.send_message(callback.message.chat.id, 'У вас нет добавленных заказов.')

        cur.close()
        conn.close()

    elif callback.data == 'complaint_elif':
        bot.send_message(callback.message.chat.id, "Пожалуйста напишите вашу жалобу:")
        bot.register_next_step_handler(callback.message, process_complaint)

    elif callback.data == 'delete_order':
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()

        user_id = callback.from_user.id
        user_projects = cur.fetchall()

        if user_projects:
            markup = types.InlineKeyboardMarkup()
            for project_id, project_name in user_projects:
                markup.add(types.InlineKeyboardButton(f"{project_name}", callback_data=f'delete_project_{project_id}'))

            bot.send_message(callback.message.chat.id, 'Выберите проект для удаления:', reply_markup=markup)
        else:
            bot.send_message(callback.message.chat.id, 'У вас нет добавленных проектов для удаления.')

        cur.close()
        conn.close()


def add_project_name(message):
    project_name = message.text.strip()
    bot.send_message(message.chat.id, 'Напишите описание своего проекта')
    bot.register_next_step_handler(message, add_description, project_name)


def add_description(message, project_name):
    project_details = message.text.strip()
    bot.send_message(message.chat.id, 'Напишите дедлайн')
    bot.register_next_step_handler(message, add_deadline, project_name, project_details)


def add_deadline(message, project_name, project_details):
    date = message.text.strip()
    date_format = "%d.%m.%Y"
    date_obj = datetime.strptime(date, date_format)
    deadline = date_obj.strftime("%Y-%m-%d")
    user_id = message.from_user.id
    status = 'pending'
    save_order(message, user_id, project_name, project_details, deadline, status)
    bot.send_message(message.chat.id, 'Проект успешно добавлен')

def process_complaint(message):
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()

    cur.close()
    conn.close()

    bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAELVJJlwm5Y8hjtLZa8Vv1pzgagp-F8AQACTAEAArd76yAze_NN5FHLKDQE')
    bot.send_message(message.chat.id,
                     "Спасибо вам за вашу жалобу. Мы рассмотрим в течении ближайшего времени и ответим на жалобу.")

def save_order(message, project_name, user_id,  project_details, deadline, status):
    customer_full_name = f'{message.from_user.first_name}, {message.from_user.last_name}'
    if status == 'pending':
        conn = create_conn('../Elif_Bot/db.sql')
    else:
        return

    cur = conn.cursor()

    cur.execute('INSERT INTO project_queue (customer_full_name, customer_id, project_name,  project_details, deadline) VALUES (?, ?, ?, ?)',
                   (customer_full_name, user_id, project_name, project_details, deadline))
    conn.commit()
    cur.close()
    conn.close()


@bot.callback_query_handler(func=lambda callback: callback.data == 'delete_order')
def delete_order(callback):
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()

    user_id = callback.from_user.id
    cur.execute("SELECT id, project_name FROM project_queue WHERE user_id=?", (user_id,))
    user_projects = cur.fetchall()

    if user_projects:
        markup = types.InlineKeyboardMarkup()
        for project_id, project_name in user_projects:
            markup.add(types.InlineKeyboardButton(f"{project_name}", callback_data=f'delete_project_{project_id}'))

        bot.send_message(callback.message.chat.id, 'Выберите проект для удаления:', reply_markup=markup)
    else:
        bot.send_message(callback.message.chat.id, 'У вас нет добавленных проектов для удаления.')

    cur.close()
    conn.close()


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('delete_project_'))
def confirm_delete_project(callback):
    project_id_to_delete = int(callback.data.split('_')[2])

    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()

    user_id = callback.from_user.id

    cur.execute("DELETE FROM project_queue WHERE id=? AND customer_id=?", (project_id_to_delete, user_id))
    conn.commit()

    cur.close()
    conn.close()

    bot.send_message(callback.message.chat.id, 'Проект успешно удален.')


bot.polling(none_stop=True)