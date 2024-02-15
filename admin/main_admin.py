import webbrowser
import datetime

import telebot
from telebot import types

from admin.configE import BOT_TOKEN, ADMINS
from Elif_Bot.database import create_table, add_stuff, delete_from_db, show_details
from Elif_Bot.database import order, completed_project, failed_project
from Elif_Bot.database import create_conn
from sqlite3 import Error
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('1868953149:AAG3Rqe9uC9RfNF62-JbCrsP2_m_kgKnkQQ')
project = []
project_details = []
messages_to_delete = []
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
        admin_main(message)
    else:
        bot.send_message(message.chat.id, 'Вы не Админ!')


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


@bot.callback_query_handler(func=lambda call: call.data == 'delete_project')
def handle_delete_project(call):
    show_all_projects(call.message.chat.id, delete=True)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_staff')
def handle_delete_staff(call):
    show_all_users(call.message.chat.id, delete=True)


def add_staff_name(message):
    user_name = message.text.strip()
    user_surname = ""

    if ' ' in user_name:
        user_name, user_surname = user_name.split(' ', 1)
    full_name = user_name + user_surname
    mess = bot.send_message(message.chat.id, "Введите ID Телеграмма Работника:")
    messages_to_delete.append(mess.message_id)
    messages_to_delete.append(message.message_id)
    bot.register_next_step_handler(mess, add_staff_sp, full_name)


def add_staff_sp(message, full_name):
    staff_id = message.text.strip()
    mess = bot.send_message(message.chat.id, "Введите специальность Работника:")
    messages_to_delete.append(mess.message_id)
    messages_to_delete.append(message.message_id)
    bot.register_next_step_handler(mess, add_staff_id, full_name, staff_id)


def add_staff_id(message, full_name, staff_id):
    staff_sp = message.text.strip()
    try:
        add_stuff(full_name, staff_id, staff_sp)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Обновленный список", callback_data=f'show_staff_{None}'))
        markup.add(types.InlineKeyboardButton("Назад", callback_data='back'))
        bot.send_message(message.chat.id, f"Сотрудник {full_name}(ID:{staff_id}) добавлен.", reply_markup=markup)
    except Exception as e:
        print(f"Произошла ошибка '{e}'")
    finally:
        messages_to_delete.append(message.message_id)
        for mess_id in messages_to_delete:
            bot.delete_message(message.chat.id, mess_id)
        messages_to_delete.clear()


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
        if project_id is None:
            project_id = 'Пока нет проектов'
        staff_detail = f"""
ID Работника: {staff_id}
Id Telegram: {staff_id_tg}
Имя: {staff_name}
Специальность: {speciality}
Проект: {project_id}
Завершены: {complete}
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


@bot.callback_query_handler(func=lambda call: call.data =="add_project")
def select_department(call):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Digital', callback_data=f'add_project_Digital')
    btn2 = types.InlineKeyboardButton('Commerce', callback_data=f'add_project_Commerce')
    btn3 = types.InlineKeyboardButton('Education', callback_data=f'add_project_Education')
    markup.add(btn1, btn2, btn3)
    bot.send_message(call.message.chat.id, 'Выберите отдел для проекта', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_project_"))
def start_second(call):
    department = call.data.split('_')[2]
    mess = bot.send_message(call.message.chat.id, "Дайте название проекту ")
    messages_to_delete.append(mess.message_id)
    messages_to_delete.append(call.message.message_id)
    bot.register_next_step_handler(call.message, add_project_name, department)


def add_project_name(message, department):
    global project
    project = message.text.strip()
    mess = bot.send_message(message.chat.id, "Напишите описание проекта: ")
    messages_to_delete.append(mess.message_id)
    messages_to_delete.append(message.message_id)
    bot.register_next_step_handler(message, project_deadline, department)


def project_deadline(message, department):
    global project_details
    project_details = message.text.strip()
    mess = bot.send_message(message.chat.id, "Напишите дедлайн в формате (Date.Month.Year) ")
    messages_to_delete.append(mess.message_id)
    messages_to_delete.append(message.message_id)
    bot.register_next_step_handler(message, insert_project, department)


def schedule_notifications(chat_id, deadline):
    current_time = datetime.date.today()
    time_difference = deadline - current_time
    days_until_deadline = time_difference.days

    if days_until_deadline == 3:
        bot.send_message(chat_id, "У вас осталось 3 дня до дедлайна!")
        return deadline
    elif days_until_deadline == 0:
        bot.send_message(chat_id, "Дедлайн сегодня!")
        return deadline
    elif days_until_deadline < 0:
        return None
    else:
        return deadline


def insert_project(message, department):
    global project
    global project_details
    date = message.text.strip()
    date_format = "%d.%m.%Y"
    try:
        deadline = datetime.datetime.strptime(date, date_format).date()
        deadline = schedule_notifications(message.chat.id, deadline)
        if deadline is None:
            bot.send_message(message.chat.id,
                             "Время не повернуть назад...")
            project_deadline(message, department)
        messages_to_delete.append(int(message.message_id))

    except ValueError:
        bot.send_message(message.chat.id, "Не удалось зарегистрировать дедлайн. Пожалуйста используйте: DD.MM.YYYY.")
        project_deadline(message, department)
        return None
    select_staff(message.chat.id)
    # bot.register_next_step_handler(message, select_staff_for_project, department, project, project_details,
    #                                deadline)
    bot.register_next_step_handler(message, added_project, department, project, project_details,
                                   deadline)

def added_project(message, department, project, project_details, deadline):
    selected_performers = message.text
    order(project, project_details, deadline, department, selected_performers)
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM projects WHERE project_details = ?", (project_details, ))
    inserted_project = cur.fetchone()
    print(inserted_project)

    cur.close()
    conn.close()

    project_info = (f"Название проекта: {inserted_project[1]}\n"
                    f"Описание проекта: {inserted_project[2]}\n"
                    f"Дедлайн: {inserted_project[7]}\n"
                    f"Отдел: {inserted_project[4]}\n"
                    f"Статус: {inserted_project[6]}\n"
                    f"Работает над проектом: {inserted_project[-1]}")

    for mess_id in messages_to_delete:
        bot.delete_message(message.chat.id, mess_id)
    messages_to_delete.clear()
    bot.send_message(message.chat.id, f"Проект добавлен:\n{project_info}")


@bot.callback_query_handler(func=lambda callback: callback.data == 'save_order')
def save_order(message, department, project_name, project_detail, deadline, status):
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()
    cur.execute("INSERT INTO projects(project_id, project_name, project_details, 'group', status,"
                "deadline) VALUES(?, ?, ?, ?, ?)",
                (project_name, project_detail, department, deadline, status))
    conn.commit()
    bot.send_message(message.chat.id, "Проект сохранен!")


def select_staff(chat_id):
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM staff')
    employees = cur.fetchall()
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for employee in employees:
        button_text = employee[1]
        button = types.KeyboardButton(button_text)
        markup.add(button)
    markup.add(types.KeyboardButton('Завершить'))
    conn.commit()
    bot.send_message(chat_id, "Выберите работников", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_project_"))
def select_project_callback(call):
    project_id = int(call.data.split('_')[2])
    delete = bool(int(call.data.split('_')[3]))
    conn = create_conn('../Elif_Bot/db.sql')
    cur = conn.cursor()
    cur.execute(
        'SELECT project_id, project_name, project_details, user_id, `group`, deadline, status, performers FROM projects WHERE project_id=?',
        (project_id,))
    project_info = cur.fetchone()
    if project_info:
        project_id, project_name, project_details, user_id, department, deadline, status, performers = project_info
        project_details_message = f"""
ID: {project_id}
Имя: {project_name}
Департамент: {department}
Описание: {project_details}
Дедлайн: {deadline}
Статус: {status}
Работает над проектом: {performers}
"""
        if delete:
            markup = types.InlineKeyboardMarkup()
            del_button_accept = types.InlineKeyboardButton("Удалить", callback_data=f'delete_project_{project_id}')
            del_button_cancel = types.InlineKeyboardButton("Оставить", callback_data=f'show_projects_{delete}')
            back_button = types.InlineKeyboardButton("Назад", callback_data='back_main')
            markup.row(del_button_accept, del_button_cancel, back_button)
            bot.send_message(call.message.chat.id, project_details_message, reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            comp_button_accept = types.InlineKeyboardButton("Завершить", callback_data=f'comp_project_{project_id}')
            fail_button_cancel = types.InlineKeyboardButton("Отказаться", callback_data=f'fail_project_{delete}')
            back_button = types.InlineKeyboardButton("Назад", callback_data='back_main')
            markup.row(comp_button_accept, fail_button_cancel, back_button)
            bot.send_message(call.message.chat.id, project_details_message, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Информация о проекте не найдена.")
    cur.close()
    conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith('comp_project_'))
def show_project_details_callback(call):
    project_id = int(call.data.split('_')[2])
    completed_project(project_id)
    bot.send_message(call.message.chat.id, "Вы завершили проект")


@bot.callback_query_handler(func=lambda call: call.data.startswith('fail_project_'))
def show_project_details_callback(call):
    project_id = int(call.data.split('_')[2])
    failed_project(project_id)
    bot.send_message(call.massage.chat.id, "Вы отказались от проекта")

def show_all_projects(chat_id, delete=False):
    try:
        conn = create_conn('../Elif_Bot/db.sql')
        cur = conn.cursor()
        cur.execute('SELECT * FROM projects WHERE status=? or status=?', ('В ожидании', 'В процессе'))
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
    # elif projects_list is None:
    #     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
    #                           text="На данный момент проектов нет.", reply_markup=None)

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


@bot.message_handler(commands=['help'])
def main(message):
    bot.send_message(message.chat.id, '<b>Help</b> <em>Information</em> ', parse_mode='html')


@bot.message_handler()
def info(message):
    if message.text.lower() in ['привет', 'hello']:
        bot.send_message(message.chat.id,
                         f'Hello {message.from_user.first_name} {message.from_user.last_name} {message.from_user.id}')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(none_stop=True)