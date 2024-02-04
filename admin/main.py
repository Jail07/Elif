import webbrowser

import telebot
import sqlite3
from telebot import types
from configE import BOT_TOKEN, ADMINS


bot = telebot.TeleBot(BOT_TOKEN)


# Function to clear all data from tables
def clear_all_data():
    conn = sqlite3.connect('ElifDB_projects.sql')  # Connect to your database
    cur = conn.cursor()
    # List of your tables
    tables = ['users', 'project', 'project_requests']
    for table in tables:
        cur.execute(f'DELETE FROM {table};')  # Delete all data from each table
    conn.commit()  # Commit the changes to the database
    conn.close()  # Close the connection to the database

@bot.message_handler(commands=['removeadmin7'])
def handle_removeadmin7(message):
    # You may want to add authentication here to make sure only authorized users can execute this
    clear_all_data()
    bot.reply_to(message, "All credentials have been removed from the database.")



def admin_view_requests(message):
    conn = sqlite3.connect('ElifDB_projects.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM project_requests WHERE status = 'pending'")
    requests = cur.fetchall()

    if not requests:
        bot.send_message(message.chat.id, "No pending project requests.")
        return

    for req in requests:
        req_id, user_id, user_name, project_name, _ = req
        bot.send_message(
            message.chat.id,
            f"Request ID: {req_id}\nUser: {user_name} (ID: {user_id})\nProject: {project_name}\n",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("Approve", callback_data=f'approve_{req_id}'),
                types.InlineKeyboardButton("Reject", callback_data=f'reject_{req_id}')
            )
        )

    cur.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_project_request_decision(call):
    action, req_id = call.data.split('_')
    conn = sqlite3.connect('ElifDB_projects.sql')
    cur = conn.cursor()

    if action == 'approve':
        cur.execute("UPDATE project_requests SET status = 'approved' WHERE id = ?", (req_id,))
        bot.answer_callback_query(call.id, "Project request approved")
    elif action == 'reject':
        cur.execute("DELETE FROM project_requests WHERE id = ?", (req_id,))
        bot.answer_callback_query(call.id, "Project request rejected")

    conn.commit()
    cur.close()
    conn.close()



def initialize_db():
    with sqlite3.connect('ElifDB.sql') as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name varchar(50), 
        surname varchar(50), 
        pass varchar(50))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS project (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        work varchar(50), 
        dl varchar(50))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS project_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        user_name TEXT, 
        user_surname TEXT, 
        project_name TEXT, 
        status TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        s_name varchar(50), 
        surname varchar(50), 
        pass varchar(50))""")
        conn.commit()

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
    check_projects = types.InlineKeyboardButton("Show projects",callback_data='show_projects')
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

    conn = sqlite3.connect('ElifDB.sql')
    cur = conn.cursor()

    cur.execute("INSERT INTO users (name, surname, pass) VALUES (?, ?, ?)", (user_name, user_surname, ""))
    conn.commit()
    cur.close()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Experts list", callback_data='show_staff'))
    bot.send_message(message.chat.id, f"User {user_name} has been added.", reply_markup=markup)

# Adding view all users function
def show_all_users(chat_id):
    conn = sqlite3.connect('ElifDB.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM users')
    users = cur.fetchall()

    info = ''
    for el in users:
        info += f'\nName: {el[1]} {el[2]}'

    cur.close()
    conn.close()

    bot.send_message(chat_id, info)

@bot.message_handler(commands=['prj', 'makeorder'])
def start_second(message):
    conn = sqlite3.connect('ElifDB_projects.sql')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS project (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work varchar(50), 
                dl varchar(50))""")
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Enter your project name ")
    bot.register_next_step_handler(message, project_name)

def project_name(message):
    global project
    project = message.text.strip()
    bot.send_message(message.chat.id, "Enter project's deadline format (Date/Month name) ")
    bot.register_next_step_handler(message, project_deadline)


def project_deadline(message):
    deadline = message.text.strip()

    conn = sqlite3.connect('ElifDB_projects.sql')
    cur = conn.cursor()

    # Insert into project table
    cur.execute("INSERT INTO project (work, dl) VALUES (?, ?)", (project, deadline))

    # Insert into project_requests table
    user_id = message.from_user.id
    user_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    cur.execute("INSERT INTO project_requests (user_id, user_name, project_name, status) VALUES (?, ?, ?, 'pending')",
                (user_id, user_name, project))

    conn.commit()
    cur.close()
    conn.close()

    mark = telebot.types.InlineKeyboardMarkup()
    # mark.add(telebot.types.InlineKeyboardButton("Our Projects", callback_data='show_projects'))
    bot.send_message(message.chat.id, "Project has been added to queue, wait until aprove ")
#     reply = mark



def show_all_projects(prj_id):
    conn = sqlite3.connect('ElifDB_projects.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM project')
    projects = cur.fetchall()

    info_prj = 'Projects:\n'
    for ell in projects:
        info_prj += (
            f"{'-' * 30}\n"
            f"Project Name: {ell[1]}\n"
            f"Project Deadline: {ell[2]}\n"
        )

    cur.close()
    conn.close()

    bot.send_message(prj_id, info_prj)

@bot.callback_query_handler(func=lambda call: call.data == 'show_project_requests' and is_admin(call.from_user.id))
def show_project_requests(call):
    conn = sqlite3.connect('ElifDB_projects.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM project_requests')
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