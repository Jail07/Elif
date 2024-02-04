import telebot
from telebot import types
from datetime import datetime
from Elif_Bot.main_database import create_conn, execute_query
from Elif_Bot.main_database import create_projects, create_users, create_departments, create_project_students
from Elif_Bot.main_database import chek_st, check_ad
from Elif_Bot.main_database import ADMINS, STAFF
from Elif_Bot.main_database import users_table, projects_table, departments_table, project_students

bot = telebot.TeleBot('6515479038:AAGL3I43ChKIEQpJQw5T8tyi5PPlcdzoq3s')
name = ""
name_project = ""
project_description = ""
date = ""

CALLBACK_LIST_STUDENT = 'list_student'
CALLBACK_LIST_PROJECT = 'list_project'
CALLBACK_ABOUT = 'about'
CALLBACK_ABOUT_PROJECT = 'about2'
CALLBACK_ADD = 'add'
CALLBACK_C = "Commerce"
CALLBACK_E = 'Education'
CALLBACK_D = 'Digital'
DEPARTMENT =""
CHECK_ADMIN = None
CHECK_ORDER = 'check_order'
NEW_ORDERS = []
NEW_NAME_PROJECT = []
NEW_DEPARTMENT = []
NEW_ABOUT = []
NEW_DEADLINE = []

# Создание соединения и выполнение запросов
conn = create_conn('students.sql')
execute_query(conn, users_table)
execute_query(conn, projects_table)
execute_query(conn, departments_table)
execute_query(conn, project_students)
# execute_query(conn, order)

if 'Elif_Bot/students.sql' == None:
    execute_query(conn, create_users)
    execute_query(conn, create_projects)
    execute_query(conn, create_project_students)
    execute_query(conn, create_departments)


@bot.message_handler(commands=['start'])
def start(message):
    if check_ad(message):
        if NEW_ORDERS != []:
            bot.send_message(message.chat.id, 'WE GET NEW ORDER')
    markup = types.InlineKeyboardMarkup()
    btn_ad = types.InlineKeyboardButton('Admin', callback_data='ADMIN')
    btn_us = types.InlineKeyboardButton('User', callback_data='USER')
    btn_st = types.InlineKeyboardButton('Staff', callback_data='STAFF')
    markup.row(btn_ad, btn_us, btn_st)
    if check_ad(message):
        btn = types.InlineKeyboardButton('Check new order', callback_data=CHECK_ORDER)
        markup.row(btn)
    btn1 = types.InlineKeyboardButton('Commerce', callback_data=CALLBACK_C)
    btn2 = types.InlineKeyboardButton(text='Education', callback_data=CALLBACK_E)
    btn3 = types.InlineKeyboardButton(text='Digital', callback_data=CALLBACK_D)
    markup.row(btn1, btn2, btn3)
    bot.send_message(message.chat.id, 'WoW', reply_markup=markup)

def user_surname(message):
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Как звать твоя дедушка?')
    bot.register_next_step_handler(message, user_department, name)

def user_department(message, name):
    surname = message.text.strip()
    bot.register_next_step_handler(message, create_student(message, name, surname))

def create_student(message, name, surname):
        global DEPARTMENT
        department = DEPARTMENT
        try:
            conn = create_conn('students.sql')
            cur = conn.cursor()
            cur.execute("INSERT INTO users (user_name, surname, department) VALUES (?, ?, ?)",
                        (name, surname, department))

            conn.commit()
            bot.send_message(message.chat.id, 'Users added successfully!')
        except Exception as e:
            print(f"Error inserting project: {e}")
        finally:
            cur.close()
            conn.close()

@bot.callback_query_handler(func=lambda callback: True)
def get_department_text(callback):
    global ADMINS
    global STAFF
    global DEPARTMENT
    conn = create_conn('students.sql')  # Замените 'students.sql' на фактический путь к вашей базе данных

    if callback.data in [CALLBACK_C, CALLBACK_E, CALLBACK_D]:
        department_text = {
            CALLBACK_C: 'Commerce',
            CALLBACK_E: 'Education',
            CALLBACK_D: 'Digital'
        }[callback.data]
        # Вызываем функцию send_info, передавая соединение
        send_info(callback.message, conn, qwerty=f'Welcome to {department_text} Department ')
        DEPARTMENT = department_text
    elif callback.data == 'ADMIN':
        ADMINS.append(callback.message.from_user.id)
        if callback.message.from_user.id in STAFF:
            STAFF.remove(callback.message.from_user.id)
        bot.send_message(callback.message.chat.id, f'Hello Admin')
        start(callback.message)
    elif callback.data == 'STAFF':
        if callback.message.from_user.id in ADMINS:
            ADMINS.remove(callback.message.from_user.id)
        STAFF.append(callback.message.from_user.id)
        bot.send_message(callback.message.chat.id, f'Hello Staff')
    elif callback.data == 'USER':
        if callback.message.from_user.id not in ADMINS:
            if callback.message.from_user.id not in STAFF:
                bot.send_message(callback.message.chat.id, 'You are User1')
        elif callback.message.from_user.id in ADMINS or STAFF:
            if callback.message.from_user.id in ADMINS:
                ADMINS.remove(callback.message.from_user.id)
            if callback.message.from_user.id in STAFF:
                STAFF.remove(callback.message.from_user.id)
            bot.send_message(callback.message.chat.id, 'You are User2')

    elif callback.data == CHECK_ORDER:
        if NEW_ORDERS == []:
            bot.send_message(callback.message.chat.id, 'NO NEW ORDERS FOUND')
        else:
            for i in range(len(NEW_ORDERS)):
                global CHECK_ADMIN
                markup = types.InlineKeyboardMarkup()
                btn = types.InlineKeyboardButton('Accept', callback_data='CHECK_TRUE')
                btn2 = types.InlineKeyboardButton('Cancel', callback_data="CHECK_FALSE")
                markup.row(btn, btn2)
                bot.send_message(callback.message.chat.id, NEW_ORDERS[i-1], reply_markup=markup)
                print(CHECK_ADMIN)

    elif callback.data == "CHECK_TRUE":
        print('TRUE')
        CHECK_ADMIN = True
        bot.register_next_step_handler(callback.message, check_project(callback.message, NEW_NAME_PROJECT, NEW_ABOUT, NEW_DEPARTMENT, NEW_DEADLINE, CHECK_ADMIN))


    elif callback.data == "CHECK_FALSE":
        print('FALSE')
        CHECK_ADMIN = False
        bot.register_next_step_handler(callback.message, check_project(callback.message, NEW_NAME_PROJECT, NEW_ABOUT, NEW_DEADLINE, NEW_DEPARTMENT, CHECK_ADMIN))


    else:
        CALLBACK_C_message(callback, conn)
    conn.close()

def get_selected_department(message):
    global DEPARTMENT
    if DEPARTMENT == CALLBACK_C:
        return 'Commerce'
    elif DEPARTMENT == CALLBACK_E:
        return 'Education'
    elif DEPARTMENT == CALLBACK_D:
        return 'Digital'
    # Добавьте другие ветви условия, если у вас есть другие отделы
    else:
        return None


def send_info(message, conn, qwerty):
    if check_ad(message):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Students', callback_data=CALLBACK_LIST_STUDENT)
        btn2 = types.InlineKeyboardButton(text='Projects', callback_data=CALLBACK_LIST_PROJECT)
        btn3 = types.InlineKeyboardButton(text='About', callback_data=CALLBACK_ABOUT)
        markup.row(btn1, btn2, btn3)
        if qwerty != None:
            bot.send_message(message.chat.id, qwerty, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Welcome', reply_markup=markup)
    elif chek_st(message):
        markup = types.InlineKeyboardMarkup()
        btn2 = types.InlineKeyboardButton(text='Projects', callback_data=CALLBACK_LIST_PROJECT)
        btn3 = types.InlineKeyboardButton(text='About', callback_data=CALLBACK_ABOUT)
        markup.row(btn2, btn3)
        bot.send_message(message.chat.id, qwerty, reply_markup=markup)
    else:
        CALLBACK_C_message2(message, qwerty)

def CALLBACK_C_message2(message, qwerty):
    chat_id = message.chat.id
    if qwerty == 'Welcome to Commerce Department ':
        bot.send_message(chat_id, 'What is the name of your project?')
        bot.register_next_step_handler(message, lambda msg: project_description(msg, department='Commerce'))
    elif qwerty == 'Welcome to Education Department ':
        bot.send_message(chat_id, 'What is the name of your project?')
        bot.register_next_step_handler(message, lambda msg: project_description(msg, department='Education'))
    elif qwerty == 'Welcome to Digital Department ':
        bot.send_message(chat_id, 'What is the name of your project?')
        bot.register_next_step_handler(message, lambda msg: project_description(msg, department='Digital'))
    else:
        bot.send_message(chat_id, 'Unknown option')

def project_description(message, department):
    global name_project
    name_project = message.text.strip()
    bot.send_message(message.chat.id, 'What is your project about?')
    bot.register_next_step_handler(message, lambda msg: deadline(msg, department=department))

def deadline(message, department):
    global project_description
    project_description = message.text.strip()
    bot.send_message(message.chat.id, 'Date of deadline:')
    bot.register_next_step_handler(message, lambda msg: finalize_order(msg, department=department))

def finalize_order(message, department):
    global date
    date = message.text.strip()
    date_format = "%d.%m.%Y"
    date_obj = datetime.strptime(date, date_format)
    your_date = date_obj.strftime("%Y-%m-%d")
    bot.send_message(message.chat.id,
                     f'Project Name: {name_project}\nProject Description: {project_description}\nDeadline: {your_date}\nDepartment: {department}')

    NEW_ORDERS.append(f'Project Name: {name_project}\nProject Description: {project_description}\nDeadline: {your_date}\nDepartment: {department}')
    NEW_NAME_PROJECT.append(name_project)
    NEW_DEPARTMENT.append(department)
    NEW_ABOUT.append(project_description)
    NEW_DEADLINE.append(your_date)

    # insert_chek_project(message, project_name=name_project, about=project_description, department=department, deadline=your_date, CHECK_ADMIN=CHECK_ADMIN)

def insert_chek_project(message, project_name, about, department, deadline,CHECK_ADMIN):
    NEW_ORDERS.append(f'Project Name: {name_project}\nProject Description: {project_description}\nDeadline: {deadline}\nDepartment: {department}')
    orderer = message.from_user.first_name + " " + message.from_user.last_name
    try:
        conn = create_conn('students.sql')
        cur = conn.cursor()
        cur.execute("INSERT INTO order (order_name, about, deadline, department, orderer) VALUES (?, ?, ?, ?, ?)", (project_name, about, deadline, department, orderer))
        conn.commit()
        delete_last_message(chat_id=message.chat.id, message_id=message.message_id)
        bot.send_message(message.chat.id, 'Project added successfully!')
    except Exception as e:
        print(f"Error inserting project: {e}")
    finally:
        cur.close()
        conn.close()

    """NEW_NAME_PROJECT.remove(project_name)
    NEW_DEPARTMENT.remove(department)
    NEW_ABOUT.remove(about)
    NEW_DEADLINE.remove(deadline)"""


    """NEW_NAME_PROJECT.append(name_project)
    NEW_DEPARTMENT.append(department)
    NEW_ABOUT.append(project_description)
    NEW_DEADLINE.append(deadline)"""

def check_project(message, project_name, about, department, deadline, CHECK_ADMIN):
    if CHECK_ADMIN:
        insert_project(message, project_name, about, department, deadline)
    elif CHECK_ADMIN == False:
        delete_last_message(chat_id=message.chat.id, message_id=message.message_id)
        bot.send_message(message.chat.id, 'NOT ADDED')
    else:
        return f'Project Name: {name_project}\nProject Description: {project_description}\nDeadline: {deadline}\nDepartment: {department}'
    """else:
        CALLBACK_C_message2(message, department)
"""
def delete_last_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")
def insert_project(message, project_name, about, department, deadline):
    try:
        conn = create_conn('students.sql')
        cur = conn.cursor()
        print(f"Trying to insert project with name: {project_name}, {about}, {department}, {deadline}")

        cur.execute("INSERT INTO projects (project_name, about,  deadline, department) VALUES (?, ?, ?, ?)", (project_name[0], about[0], deadline[0], department[0]))
        conn.commit()
        delete_last_message(chat_id=message.chat.id, message_id=message.message_id)
        bot.send_message(message.chat.id, 'Project added successfully!')
        NEW_NAME_PROJECT.remove(project_name[0])
        NEW_DEPARTMENT.remove(department[0])
        NEW_ABOUT.remove(about[0])
        NEW_DEADLINE.remove(deadline[0])

    except Exception as e:
        print(f"Error inserting project: {e}")
    finally:
        cur.close()
        conn.close()


@bot.callback_query_handler(func=lambda callback: True)
def CALLBACK_C_message(callback, conn):
    chat_id = callback.message.chat.id
    cur = conn.cursor()
    # Получите отдел (department), выбранный пользователем
    selected_department = get_selected_department(callback.message)
    if callback.data == CALLBACK_LIST_STUDENT:
        if check_ad(callback.message):
            try:
                cur.execute('SELECT * FROM users')
                users = cur.fetchall()
                print(users)
                markup = types.InlineKeyboardMarkup()
                # Создайте кнопки только для студентов из выбранного отдела
                for user in users:
                    if user[3] == selected_department:
                        btn = types.InlineKeyboardButton(f'{user[0]}: {user[1]} {user[2]}, {user[3]}, {user[4]}', callback_data=f'{CALLBACK_ABOUT_PROJECT}_{user[0]}')
                        markup.row(btn)

                btn = types.InlineKeyboardButton('add_student', callback_data=CALLBACK_ADD)
                markup.row(btn)
                bot.send_message(chat_id, 'Click ', reply_markup=markup)
            except Exception as e:
                print(f"Error fetching users: {e}")

    elif callback.data == CALLBACK_LIST_PROJECT:
        if check_ad(callback.message) or chek_st(callback.message):
            cur.execute('SELECT * FROM projects')
            projects = cur.fetchall()
            markup = types.InlineKeyboardMarkup()

            for project in projects:
                print(project[4])
                if project[4] == selected_department:

                    btn = types.InlineKeyboardButton(project[1], callback_data=f'{CALLBACK_ABOUT_PROJECT}_{project[0]}')
                    markup.row(btn)

            bot.send_message(chat_id, 'Projects:', reply_markup=markup)
    elif callback.data == CALLBACK_ABOUT:
        cur.execute('SELECT * FROM departments')
        departments = cur.fetchall()
        for department in departments:
            if department[1] == selected_department:
                bot.send_message(chat_id, f'{department[3]}')


    elif callback.data.startswith(CALLBACK_ABOUT_PROJECT):
        if check_ad(callback.message) or chek_st(callback.message):
            project_id = callback.data.split('_')[1]
            try:
                cur.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
                project_info = cur.fetchone()
                if project_info is not None and len(project_info) >= 4:
                    cur.execute('SELECT * FROM users WHERE id IN (?)', (project_info[3],))
                    students = cur.fetchall()
                    students_info = "\n".join([f'{student[1]} {student[2]}' for student in students])
                    cur.execute('SELECT * FROM project_students')
                    project_students = cur.fetchall()
                    list_st = []
                    for students_list in project_students:
                        print(students_list, project_info)
                        if students_list[0] == project_info[0]:
                            list_st.append(students_list[1])
                            print(list_st)
                    student_name_list = ''

                    for student_id in list_st:
                        cur.execute('SELECT * FROM users WHERE id IN (?)', (student_id,))
                        student_name = cur.fetchall()
                        student = " ".join((student_name[0][1], student_name[0][2]))
                        student_name_list += (f'\n{student}')
                    print(student_name_list)
                    if student_name_list == '':
                        student_name_list = "We haven't student for this project"
                    bot.send_message(chat_id, f"""
Project: {project_info[1]}
Description: {project_info[2]}
Deadline: {project_info[4]}
Students: {(student_name_list)}
                    """)
                else:
                    bot.send_message(chat_id, "Проект не найден или некорректная структура данных.")
            except Exception as e:
                print(f"Error fetching project info: {e}")

    elif callback.data == CALLBACK_ADD:
        if check_ad(callback.message):
            bot.send_message(callback.message.chat.id, 'Как тебя звать?')
            bot.register_next_step_handler(callback.message, user_surname)

    elif callback.data == 'ADMIN':
        ADMINS.append(callback.message.from_user.id)

    else:
        bot.send_message(chat_id, 'Неизвестный выбор')

    cur.close()
    conn.close()

if __name__ == "__main__":
    bot.polling(none_stop=True)
