import webbrowser
import datetime

import telebot
from telebot import types

from configE import BOT_TOKEN, ADMINS
from Elif_Bot.database import create_table, add_stuff, delete_from_db, show_details
from Elif_Bot.database import create_conn
from sqlite3 import Error
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(BOT_TOKEN)
project = []
project_details = []
user_message_stack = {}


def execute_query(query, data=None):
    try:
        conn = create_conn('../Elif_Bot/db.sql')
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
    conn = create_conn('../Elif_Bot/db.sql')
    if not conn:
        return
    try:
        tables = ['users', 'project', 'project_requests']
        for table in tables:
            execute_query(f'DELETE FROM {table};')
    finally:
        conn.close()


@bot.message_handler(commands=['removeadmin7'])
def handle_removeadmin7(message):
    # You may want to add authentication here to make sure only authorized users can execute this
    clear_all_data()
    bot.reply_to(message, "Все реквизиты админа были удалены из базы данных.")


def delete_last_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка в удалении сообщении: {e}")


def initialize_db():
    conn = create_conn('../Elif_Bot/db.sql')
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
    else:
        bot.send_message(message.chat.id, 'Вы не Админ!')


def clear_message_stack(chat_id):
    if chat_id in user_message_stack:
        for message in user_message_stack[chat_id]:
            bot.delete_message(chat_id, message.message_id)
        user_message_stack[chat_id] = []


def send_new_message(chat_id, text, reply_markup=None):
    clear_message_stack(chat_id)  # Очистим стек сообщений перед отправкой нового
    # Удаляем предыдущее сообщение, если оно есть
    if chat_id in user_message_stack and user_message_stack[chat_id]:
        bot.delete_message(chat_id, user_message_stack[chat_id].pop().message_id)
    # Отправляем новое сообщение
    message = bot.send_message(chat_id, text, reply_markup=reply_markup)
    if chat_id not in user_message_stack:
        user_message_stack[chat_id] = []
    user_message_stack[chat_id].append(message)
# Admin functionality
def admin_main(message):
    markup = types.InlineKeyboardMarkup()
    project_mgmt_button = types.InlineKeyboardButton("Управление проектами", callback_data='project_mgmt')
    staff_mgmt_button = types.InlineKeyboardButton("Управление сотрудниками", callback_data='staff_mgmt')
    markup.add(project_mgmt_button, staff_mgmt_button)
    bot.send_message(message.chat.id, "Добро пожаловать Админ! Выберите категорию:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'project_mgmt')
def handle_project_mgmt(call):
    markup = types.InlineKeyboardMarkup()
    add_project_button = types.InlineKeyboardButton("Добавить проект", callback_data='add_project')
    show_projects_button = types.InlineKeyboardButton("Показать проекты", callback_data='show_projects')
    back_button = types.InlineKeyboardButton("Назад", callback_data='back')
    del_prj = types.InlineKeyboardButton("Удалить проект", callback_data='delete_project')
    markup.add(add_project_button, show_projects_button, del_prj, back_button)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Управление проектами:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'staff_mgmt')
def handle_staff_mgmt(call):
    markup = types.InlineKeyboardMarkup()
    add_staff_button = types.InlineKeyboardButton("Добавить сотрудника", callback_data='add_staff')
    del_staff_button = types.InlineKeyboardButton("Удалить сотрудника", callback_data='delete_staff')
    show_staff_button = types.InlineKeyboardButton("Показать сотрудников", callback_data=f'show_staff_{None}')
    back_button = types.InlineKeyboardButton("Назад", callback_data='back')
    markup.add(add_staff_button, del_staff_button, show_staff_button, back_button)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Управление сотрудниками:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'add_staff')
def handle_add_staff(call):
    bot.send_message(call.message.chat.id, "Напишите имя сотрудника которого вы хотите добавить:")
    bot.register_next_step_handler(call.message, add_staff_name)

@bot.callback_query_handler(func=lambda call: call.data == 'back')
def handle_back(call):
    admin_main(call.message)
    delete_last_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def handle_back_main(callback):
    chat_id = callback.message.chat.id
    clear_message_stack(chat_id)

    current_message_id = callback.message.message_id

    bot.delete_message(chat_id, current_message_id)

    if chat_id in user_message_stack and user_message_stack[chat_id]:
        bot.delete_message(chat_id, user_message_stack[chat_id][0].message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_staff_"))
def handle_show_staff(call):
    after_delete = call.data.split('_')[2]
    if after_delete is None:
        show_all_users(call.message.chat.id)
    else:
        delete_last_message(call.message.chat.id, call.message.message_id)
        show_all_users(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_projects_"))
def handle_show_projects(call):
    after_delete = call.data.split('_')[2]
    if after_delete is None:
        show_all_projects(call.message.chat.id)
    else:
        delete_last_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'add_project')
def handle_add_project(call):
    bot.send_message(call.message.chat.id, "Дайте название проекту ")
    bot.register_next_step_handler(call.message, add_project_name)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_project')
def handle_delete_project(call):
    show_all_projects(call.message.chat.id, delete=True)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_staff')
def handle_delete_staff(call):
    show_all_users(call.message.chat.id, delete=True)


def add_staff_name(message):
    user_name = message.text.strip()
    user_surname = ""

    # Check if the user has a last name
    if ' ' in user_name:
        user_name, user_surname = user_name.split(' ', 1)
    full_name = user_name + user_surname
    bot.send_message(message.chat.id, "Введите ID Телеграмма Работника: ")
    bot.register_next_step_handler(message, add_staff_sp, full_name)


def add_staff_sp(message, full_name):
    staff_id = message.text.strip()
    bot.send_message(message.chat.id, "Введите специальность Работника: ")
    bot.register_next_step_handler(message, add_staff_id, full_name, staff_id)


def add_staff_id(message, full_name, staff_id):
    staff_sp = message.text.strip()
    try:
        add_stuff(full_name, staff_id, staff_sp)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Обновленный список", callback_data=f'show_staff_{None}'))
        bot.send_message(message.chat.id, f"Сотрудник {full_name}(ID:{staff_id}) добавлен.", reply_markup=markup)
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
    except Exception as e:
        print(f"Произошла ошибка '{e}'")


def show_all_users(chat_id, delete=False):
    try:
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()

        cur.execute('SELECT * FROM staff')
        users = cur.fetchall()
        markup = InlineKeyboardMarkup()
        for el in users:
            if el[3] is None:
                button_text = f'Имя: {el[1]}, ID: {el[0]}'
                button = InlineKeyboardButton(button_text, callback_data=f'select_staff_{el[0]}_{int(delete)}')
            else:
                button_text = f'\nИмя: {el[1]}, Специальность: {el[3]}'
                button = InlineKeyboardButton(button_text, callback_data=f'select_staff_{el[0]}_{int(delete)}')
            markup.add(button)
        if not users:
            bot.send_message(chat_id, "Нет Работников ")
        else:
            bot.send_message(chat_id, "Выберите Работника", reply_markup=markup)

    except Error as e:
        print(f"Произошла ошибка '{e}'")

    finally:
        cur.close()
        conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_staff_"))
def staff_detail_handler(call):
    staff_id = int(call.data.split('_')[2])
    delete = bool(int(call.data.split('_')[3]))
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()
    cur.execute('SELECT full_name, staff_id_tg, speciality, project_id, complete, mistakes FROM staff WHERE id=?', (staff_id,))
    staff_info = cur.fetchone()
    if staff_info:
        staff_name, staff_id_tg, speciality, project_id, complete, mistakes = staff_info
        staff_detail = f"""
ID: {staff_id}
Id Telegram: {staff_id_tg}
Имя: {staff_name}
Специальность: {speciality}
Проект: {project_id}
Завершены:{complete}
Провалы: {mistakes}"""
        if delete:
            markup = types.InlineKeyboardMarkup()
            del_button_accept = types.InlineKeyboardButton("Уволить", callback_data=f'delete_staff_{staff_id}')
            del_button_cancel = types.InlineKeyboardButton("Оставить", callback_data=f'show_staff_{delete}')
            markup.row(del_button_accept, del_button_cancel)
            bot.send_message(call.message.chat.id, staff_detail, reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, staff_detail)
    else:
        bot.send_message(call.message.chat.id, "Информация о работнике не найдена.")
    cur.close()
    conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_staff_'))
def delete_staff(call):
    delete_last_message(call.message.chat.id, call.message.message_id)
    staff_id = int(call.data.split('_')[2])
    delete_from_db('staff', staff_id)
    bot.send_message(call.message.chat.id, 'Сотрудник уволен')


@bot.message_handler(commands=['prj', 'makeorder'])
def start_second(message):
    bot.send_message(message.chat.id, "Дайте название проекту ")
    bot.register_next_step_handler(message, add_project_name)


def add_project_name(message):
    global project
    project = message.text.strip()
    bot.send_message(message.chat.id, "Напишите описание проекта: ")
    bot.register_next_step_handler(message, project_deadline)


def project_deadline(message):
    global project_details
    project_details = message.text.strip()
    bot.send_message(message.chat.id, "Напишите дедлайн в формате (Date.Month.Year) ")
    bot.register_next_step_handler(message, insert_project)


def check_deadline(message, deadline):
    current_date = datetime.date.today()
    print(current_date)
    print(deadline)
    if current_date < deadline:
        print('время еще есть')
    elif current_date > deadline:
        print('Время истекло')
    elif current_date == deadline:
        print('Время уже почти')
    else:
        print('Не правильно введен дата')


def insert_project(message):
    global project
    global project_details
    date = message.text.strip()
    date_format = "%d.%m.%Y"
    try:
        deadline = datetime.datetime.strptime(date, date_format).date()
        # print(date_obj)
        # deadline = datetime.datetime.strftime(date_obj, "%Y-%m-%d").date()
        check_deadline(message, deadline)
    except ValueError:
        bot.send_message(message.chat.id, "Не удалось зарегистрировать дедлайн. Пожалуйста используйте: DD.MM.YYYY.")
        project_deadline(message)
        return

    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()
    # Insert into project table
    cur.execute("INSERT INTO projects (project_name, project_details, deadline, status) VALUES (?, ?, ?, ?)",
                (project, project_details, deadline, 'pending'))
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Проект добавлен")


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_project_"))
def select_project_callback(call):
    project_id = int(call.data.split('_')[2])
    delete = bool(int(call.data.split('_')[3]))
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()
    cur.execute(
        'SELECT project_id, project_name, project_details, user_id, department, deadline FROM projects WHERE project_id=?',
        (project_id,))
    project_info = cur.fetchone()
    if project_info:
        project_id, project_name, project_details, user_id, department, deadline = project_info
        project_details_message = f"""
ID: {project_id}
Имя: {project_name}
Id Telegram: {user_id}
Департамент: {department}
Дедлайн: {deadline}"""
        if delete:
            markup = types.InlineKeyboardMarkup()
            del_button_accept = types.InlineKeyboardButton("Удалить", callback_data=f'delete_project_{project_id}')
            del_button_cancel = types.InlineKeyboardButton("Оставить", callback_data=f'show_projects_{delete}')
            markup.row(del_button_accept, del_button_cancel)
            bot.send_message(call.message.chat.id, project_details_message, reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, project_details_message)

    else:
        bot.send_message(call.message.chat.id, "Информация о проекте не найдена.")
    cur.close()
    conn.close()


def show_all_projects(chat_id, delete=False):
    try:
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM projects')
        projects_list = cur.fetchall()

        markup = InlineKeyboardMarkup(row_width=1)

        for i, project in enumerate(projects_list):
            button_text = f"{project[1]} - ID: {project[0]}"
            if delete:
                button = InlineKeyboardButton(button_text, callback_data=f"select_project_{project[0]}_{int(delete)}")
            else:
                button = InlineKeyboardButton(button_text, callback_data=f"select_project_{project[0]}_{int(delete)}")
            markup.add(button)

        markup.add(types.InlineKeyboardButton("Назад", callback_data='back_main'))
        if not projects_list:
            bot.send_message(chat_id, "На данный момент проектов нет")
        else:
            bot.send_message(chat_id, "Выберите проект:", reply_markup=markup)

        cur.close()
        conn.close()

    except Error as e:
        print(f"Error fetching projects: {e}")


# @bot.callback_query_handler(func=lambda call: call.data.startswith('show_project'))
# def show_project_details_callback(call):
#     project_id = int(call.data.split('_')[2])
#     show_project_details(call.message.chat.id, project_id)


# def show_project_details(chat_id, project_id):
#     print(f"show_project_details called with chat_id={chat_id}, project_id={project_id}")  # Add this line
#     project_name, project_details = get_project_details(project_id)
#
#     if project_details:
#         bot.send_message(chat_id, f"Details for project '{project_name}':\n{project_details}")
#     else:
#         bot.send_message(chat_id, f"Details for project '{project_name}' not available.")


@bot.callback_query_handler(func=lambda call: call.data == 'show_projects')
def show_projects_callback(call):
    markup = InlineKeyboardMarkup(row_width=1)
    projects_list = show_all_projects(call.message.chat.id)

    if projects_list:
        for project_name in projects_list:
            markup.add(InlineKeyboardButton(project_name, callback_data=f'show_project:{project_name}'))

        markup.add(InlineKeyboardButton("Назад в главное меню", callback_data='back_main'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите проект:", reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="На данный момент проектов нет.", reply_markup=None)

def get_project_name(project_id):
    try:
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()

        cur.execute("SELECT project_name FROM projects WHERE id = ?", (project_id,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        return result[0] if result else None
    except Error as e:
        print(f"Error getting project name: {e}")
        return None


def get_project_details(project_id):
    try:
        show_details(project_id)
        result = show_details(project_id)
        return result if result else (None, None)
    except Error as e:
        print(f"Error getting project details: {e}")
        return None, None


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_project_'))
def delete_project_callback(call):
    delete_last_message(call.message.chat.id, call.message.message_id)
    project_id = int(call.data.split('_')[2])
    delete_from_db('projects', project_id)
    bot.send_message(call.message.chat.id, 'Проект удалён')


def delete_project(message, project_id):
    try:
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()

        # Get project name for logging or further use if needed
        cur.execute("SELECT project_name FROM projects WHERE id = ?", (project_id,))
        project_name = cur.fetchone()[0]

        # Delete project from projects table
        cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()

        cur.close()
        conn.close()

        bot.send_message(message.chat.id, f"Проект '{project_name}' удален.")
        show_all_projects(message.chat.id, delete=True)  # Show the updated list of projects

    except Error as e:
        print(f"Error deleting project: {e}")


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
        bot.send_message(message.chat.id,
                         f'Hello {message.from_user.first_name} {message.from_user.last_name} {message.from_user.id}')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')


# Make it infinite
bot.polling(none_stop=True)