import sqlite3
import telebot
import threading
from sqlite3 import Error


admin = '''CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    full_name VARCHAR(50)
);
'''

users = '''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        chat_id INTEGER
    )
'''

staff = '''CREATE TABLE IF NOT EXISTS staff(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    full_name VARCHAR(100),
    staff_id_tg INTEGER,
    speciality VARCHAR(100),
    project_id INTEGER,
    complete INTEGER, 
    mistakes INTEGER,
    user_id INTEGER,
    `group` TEXT, 
    contacts TEXT,
    project_status TEXT,
    project_history TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
'''

projects = '''CREATE TABLE IF NOT EXISTS projects(
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(50), 
    project_details VARCHAR(50),
    user_id INTEGER,
    `group` TEXT,
    department TEXT,
    status TEXT,
    deadline DATE
);
'''

project_staff = """CREATE TABLE IF NOT EXISTS project_staff (
    project_id INTEGER,
    staff_id INTEGER,
    `group` TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (staff_id) REFERENCES staff(id)
);
"""


def execute_query(connection, query, parameters=()):
    cursor = connection.cursor()
    cursor.execute(query, parameters)
    connection.commit()
    cursor.close()


# Создание таблиц
def create_table(conn):
    cur = conn.cursor()
    cur.execute(users)
    cur.execute(staff)
    cur.execute(admin)
    cur.execute(projects)
    cur.execute(project_staff)
    conn.commit()
    return "ТАБЛИЦЫ УСПЕШНО СОЗДАНЫ"


def create_conn(path):
    conn = None
    try:
        conn = sqlite3.connect(path)
        print("Подключение к базе данных SQLite прошло успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")
    return conn


# Проверка существования пользователя в базе данных
def exist_user(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    conn = sqlite3.connect('db.sql')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        conn.commit()

    cursor.close()
    conn.close()


# Добавление сотрудника
def add_stuff(full_name, id_staff, speciality):
    with sqlite3.connect('db.sql') as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO staff(full_name, staff_id_tg, speciality, complete, mistakes ) VALUES(?, ?, ?, ?, ?)", (full_name, id_staff, speciality, 0,0))
        conn.commit()


# Закидывает данные заказа в очередь
def order(project_name, project_detail):
    conn = sqlite3.connect('db.sql')
    status = 'В ожидании'
    cursor = conn.cursor()
    cursor.execute("INSERT INTO projects(project_name, project_details, status) VALUES(?, ?, ?)", (project_name,
                                                                                                   project_detail,
                                                                                                   status))
    conn.commit()
    cursor.close()
    conn.close()


# После нажатия кнопки собирает имена проектов которые еще не взять кем-то
def show_projects():
    conn = sqlite3.connect('db.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT project_name FROM projects")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return projects


# Показывает детали выбранного проекта
def show_details(project_id):
    conn = sqlite3.connect('db.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT project_details FROM projects WHERE project_id=?", (project_id,))
    details = cursor.fetchone()
    cursor.close()
    conn.close()
    return details


# Проект разрабатывается сотрудниками и данные переходят в базу сотрудников
def approved_project(project_id):
    conn = sqlite3.connect('db.sql')
    status = "В процессе"
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO project_staff(project_id, staff_id)
        SELECT project_id, id
        FROM projects, staff
        WHERE projects.project_id = ? AND staff.project_id IS NULL
    ''', (project_id,))
    cursor.execute("UPDATE staff SET project_status=? WHERE id=?", (status, project_id,))
    conn.commit()
    cursor.close()
    conn.close()


# При провале обновляется статус и увеличиваются косяки
def failed_project(project_id):
    conn = sqlite3.connect('db.sql')
    status = 'Провален'
    cursor = conn.cursor()
    cursor.execute(f"UPDATE staff SET project_status=? WHERE id=?", (status, project_id,))
    cursor.execute("UPDATE staff SET mistakes = mistakes + 1")
    conn.commit()
    cursor.close()
    conn.close()


# Обновлятется статус когда проект успешен
def completed_project(project_id):
    conn = sqlite3.connect('db.sql')
    status = 'Завершен'
    cursor = conn.cursor()
    cursor.execute(f"UPDATE staff SET project_status=? WHERE id=?", (status, project_id,))
    conn.commit()
    cursor.close()
    conn.close()


# Обновление данных проекта
def update_project(project_id, project_name, project_details):
    conn = sqlite3.connect('db.sql')
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET project_name=?, project_details=? WHERE project_id=?", (project_name, project_details, project_id))
    conn.commit()
    cursor.close()
    conn.close()


# Удаление из базы данных
# Updated function to delete from database with dynamic primary key column names
def delete_from_db(table, index):
    conn = sqlite3.connect('db.sql')
    cursor = conn.cursor()

    # Map of table names to their primary key column names
    table_primary_keys = {
        'admin': 'id',
        'users': 'user_id',
        'staff': 'id',
        'projects': 'project_id',
        'project_staff': 'project_id'  # Assuming you want to delete by project_id, adjust if needed
    }

    # Get the primary key column name for the given table, default to 'id' if table is not found in the map
    primary_key_column = table_primary_keys.get(table, 'id')

    # Construct and execute the delete statement using the correct primary key column
    delete_statement = f"DELETE FROM {table} WHERE {primary_key_column}=?"
    cursor.execute(delete_statement, (index,))

    conn.commit()
    cursor.close()
    conn.close()




# Функция Объявления
# @bot.message_handler(commands=['send'])
# def handle_send(message):
#     chat_id = message.chat.id
#     user_id = message.from_user.id
#
#     # Проверяем, является ли пользователь администратором
#     conn = sqlite3.connect('db.sql')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
#     admin_user = cursor.fetchone()
#
#     if admin_user:
#         bot.send_message(chat_id, "Отправь мне текст сообщения для рассылки.")
#         bot.register_next_step_handler(message, send_to_all_users)
#     else:
#         bot.send_message(chat_id, "Вы не администратор.")
#
#
# # Отправка сообщения всем пользователям
# def send_to_all_users(message):
#     text = message.text
#     conn = sqlite3.connect('db.sql')
#     cursor = conn.cursor()
#
#     # Получаем список всех пользователей из базы данных
#     cursor.execute('SELECT * FROM users')
#     all_users = cursor.fetchall()
#
#     # Отправляем сообщение каждому пользователю
#     for user in all_users:
#         user_id = user[0]
#         bot.send_message(user_id, f"Администратор отправил сообщение: {text}")
#
#     bot.send_message(message.chat.id, "Сообщение успешно отправлено всем пользователям.")
#
#     cursor.close()
#     conn.close()

