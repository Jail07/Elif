import webbrowser
from datetime import datetime

import telebot
import sqlite3
from telebot import types
from admin.configE import BOT_TOKEN, ADMINS
from database import create_table, add_stuff, approved_project, delete_db
from database import temp_proj_db, users_db, stuff_db, admin_db, project_students, projects_list
from database import create_conn
from sqlite3 import Error



bot = telebot.TeleBot(BOT_TOKEN)
project = []
project_details = []

def execute_query(query, data=None):
    try:
        conn = create_conn('../db.sql')
        cur = conn.cursor()
        if data:
            cur.execute(query, data)
        else:
            cur.execute(query)
        conn.commit()
        cur.close()
        return True
    except Error as e:
        print(f"Error executing query: {e}")
        return False

def clear_all_data():
    conn = create_conn('../db.sql')
    if not conn:
        return
    try:
        tables = ['users', 'project', 'project_requests']
        for table in tables:
            execute_query(f'DELETE FROM {table};')
        print("Query executed successfully")
    finally:
        conn.close()

@bot.message_handler(commands=['removeadmin7'])
def handle_removeadmin7(message):
    # You may want to add authentication here to make sure only authorized users can execute this
    clear_all_data()
    bot.reply_to(message, "All credentials have been removed from the database.")

def admin_view_requests(message):
    try:
        conn = create_conn('../db.sql')
        cur = conn.cursor()
        cur.execute("SELECT * FROM project_queue WHERE status = 'pending'")
        requests = cur.fetchall()

        if not requests:
            bot.send_message(message.chat.id, "No pending project requests.")
            return None
        print(requests)
        for req in requests:
            print(req)
            user_id = message.from_user.id
            req_id, user_name, project_name, project_details, deadline, status = req
            bot.send_message(
                message.chat.id,
                f"Request ID: {req_id}\nUser: {user_name} (ID: {user_id})\nProject: {project_name}\nAbout: {project_details}\nDeadline: {deadline}",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("Approve", callback_data=f'approve_{req_id}'),
                    types.InlineKeyboardButton("Reject", callback_data=f'reject_{req_id}')
                )
            )

        cur.close()
        conn.close()
        print("Запрос выполнен успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")

def delete_last_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_project_request_decision(call):
    action, req_id = call.data.split('_')
    try:
        conn = create_conn('../db.sql')
        cur = conn.cursor()

        if action == 'approve':
            cur.execute("SELECT * FROM project_queue WHERE id = ?", (req_id,))
            requests = cur.fetchall()

            if not requests:
                bot.send_message(call.message.chat.id, "No pending  requests.")
                return None
            for req in requests:
                user_id = call.message.from_user.id
                req_id, user_name, project, project_details, deadline, status = req
            execute_query(
                "INSERT INTO projects (customer_full_name, customer_id, project_name, project_details, deadline) VALUES (?, ?, ?, ?, ?)",
                (user_name, user_id, project, project_details, deadline))

            execute_query("DELETE FROM project_queue WHERE id = ?", (req_id,))
            delete_last_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            bot.answer_callback_query(call.id, "Project request approved")
        elif action == 'reject':
            execute_query("DELETE FROM project_queue WHERE id = ?", (req_id,))
            bot.answer_callback_query(call.id, "Project request rejected")
    except Error as e:
        bot.answer_callback_query(call.id, f"Error processing request, Error {e}")

    finally:
        cur.close()
        conn.close()


def initialize_db():
    conn = create_conn('../db.sql')
    create_table(conn)


initialize_db()
# Admin Check
def is_admin(user_id):
    return user_id in ADMINS
# Welcome text
@bot.message_handler(commands=["start", 'hello', 'привет'])
def main(message):
    user_id = message.from_user.id

    if is_admin(user_id):
        # Admin functionality
        admin_main(message)

# Admin functionality
def admin_main(message):
    bot.send_message(message.chat.id, f'Hello Admin {message.from_user.first_name} {message.from_user.last_name}, choose what interests you.')
    show_staff = types.InlineKeyboardButton("Show staff", callback_data='show_staff')
    check_projects = types.InlineKeyboardButton("Show projects", callback_data='show_projects')
    add_user_button = types.InlineKeyboardButton("Add staff", callback_data='add_staff')
    show_prj_requests_button = types.InlineKeyboardButton("Show Project Requests", callback_data='show_project_requests')
    markup = types.InlineKeyboardMarkup().add(add_user_button, check_projects, show_staff, show_prj_requests_button)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

# Callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == 'add_staff' and is_admin(user_id):
        bot.send_message(call.message.chat.id, "Enter the name of the staff you want to add:")
        bot.register_next_step_handler(call.message, add_user_name)
    elif call.data == 'show_staff':
        show_all_users(call.message.chat.id)
    elif call.data == 'show_projects':
        show_all_projects(call.message.chat.id)
    elif call.data == 'show_project_requests' and is_admin(user_id):
        admin_view_requests(call.message)

# Function to add a user

def add_user_name(message):
    user_name = message.text.strip()
    user_surname = ""

    # Check if the user has a last name
    if ' ' in user_name:
        user_name, user_surname = user_name.split(' ', 1)
    full_name = user_name + user_surname
    try:
        add_stuff(full_name, 0)

        # conn = create_conn('db.sql')
        # cur = conn.cursor()
        # cur.execute("INSERT INTO staff (full_name, id_project) VALUES (?, ?)", (full_name, ''))
        #
        # conn.commit()
        # cur.close()
        # conn.close()

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Experts list", callback_data='show_staff'))
        bot.send_message(message.chat.id, f"User {user_name} has been added.", reply_markup=markup)
        print('Good')
    except Exception as e:
        print(e)

# Adding view all users function
def show_all_users(chat_id):
    try:
        conn = create_conn('../db.sql')
        cur = conn.cursor()

        cur.execute('SELECT * FROM staff')
        users = cur.fetchall()

        info = ''
        for el in users:
            info += f'\nName: {el[1]} {el[2]}'

        if info == '':
            info = "We don't have staff"

        cur.close()
        conn.close()

        bot.send_message(chat_id, info)
        print("Запрос выполнен успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")

@bot.message_handler(commands=['prj', 'makeorder'])
def start_second(message):
    bot.send_message(message.chat.id, "Enter your project name ")
    bot.register_next_step_handler(message, add_project_name)

def add_project_name(message):
    global project
    project = message.text.strip()
    bot.send_message(message.chat.id, "About: ")
    bot.register_next_step_handler(message, project_deadline)

def project_deadline(message):
    global project_details
    project_details = message.text.strip()
    bot.send_message(message.chat.id, "Enter project's deadline format (Date.Month.Year) ")
    bot.register_next_step_handler(message, insert_project)


def insert_project(message, user_name=None, user_id2=None, project_name=None, project_about=None, deadline2=None):
    global project
    global project_details
    date = message.text.strip()
    date_format = "%d.%m.%Y"
    date_obj = datetime.strptime(date, date_format)
    deadline = date_obj.strftime("%Y-%m-%d")
    user_id1 = message.from_user.id
    user = f"{message.from_user.first_name} {message.from_user.last_name}"
    if project_name and project_about and user_name and deadline2 and user_id2 is not None:
        project = project_name
        project_details = project_about
        user = user_name
        user_id1 = user_id2
        deadline = deadline2

    conn = create_conn('../db.sql')
    cur = conn.cursor()
    # Insert into project table
    cur.execute("INSERT INTO project_queue (customer_full_name, customer_id project_name, project_details, deadline, status) VALUES (?, ?, ?, ?, ?)", (user, user_id1, project, project_details, deadline, 'pending'))
    # Insert into project_requests table
    # user_id = message.from_user.id
    # user_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    # cur.execute("INSERT INTO project_requests (user_id, user_name, project_name, status) VALUES (?, ?, ?, 'pending')",
    #             (user_id, user_name, project))

    conn.commit()
    cur.close()
    conn.close()

    mark = telebot.types.InlineKeyboardMarkup()
    # mark.add(telebot.types.InlineKeyboardButton("Our Projects", callback_data='show_projects'))
    bot.send_message(message.chat.id, "Project has been added to queue, wait until aprove ")
#     reply = mark



def show_all_projects(prj_id):
    try:
        conn = create_conn('../db.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM projects')
        projects_list = cur.fetchall()

        info_prj = 'Projects:\n'
        i = 0
        for ell in projects_list:
            info_prj += (
                f"{'-' * 30}\n"
                f"Project Name: {ell[1]}\n"
                f"Project Deadline: {ell[4]}\n")
            i += 1

        if i == 0:
            info_prj += "We don't have any projects"



        cur.close()
        conn.close()

        bot.send_message(prj_id, info_prj)
        print("Запрос выполнен успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")




@bot.callback_query_handler(func=lambda call: call.data == 'show_project_requests' and is_admin(call.from_user.id))
def show_project_requests(call):
    try:
        conn = create_conn('../db.sql')
        cur = conn.cursor()

        cur.execute('SELECT * FROM project_queue')
        project_requests = cur.fetchall()

        info_prj_req = 'Project Requests:\n'
        for req in project_requests:
            info_prj_req += (
                f"{'-' * 30}\n"
                f"User ID: {req[1]}\n"
                f"User Name: {req[2]}\n"
                f"Project Name: {req[3]}\n"
            )

        cur.close()
        conn.close()

        bot.send_message(call.message.chat.id, info_prj_req)
        print("Запрос выполнен успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")


# Open Website
@bot.message_handler(commands=['site', 'website'])
def site(message):
    webbrowser.open('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

# Help option
@bot.message_handler(commands=['help'])
def main(message):
    bot.send_message(message.chat.id, '<b>Help</b> <em>Information</em> ', parse_mode='html')

# Additional greeting function
@bot.message_handler()
def info(message):
    if message.text.lower() in ['привет', 'hello']:
        bot.send_message(message.chat.id, f'Hello {message.from_user.first_name} {message.from_user.last_name} ')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')

# Make it infinite
bot.polling(none_stop=True)