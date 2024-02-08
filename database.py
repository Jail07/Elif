import sqlite3
from sqlite3 import Error


users_db = '''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    full_name VARCHAR(100), 
    project_name VARCHAR(50), 
    project_details VARCHAR(50), 
    project_history VARCHAR(50), 
    complaints VARCHAR(200),
    contact INTEGER
);
'''

stuff_db = '''CREATE TABLE IF NOT EXISTS staff(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    full_name VARCHAR(100),
    id_project INTEGER, 
    mistakes INTEGER,
    FOREIGN KEY (id_project) REFERENCES projects(id)
);
'''

admin_db = '''CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    full_name VARCHAR(50)
);
'''

temp_proj_db = '''CREATE TABLE IF NOT EXISTS project_queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_full_name TEXT,
    customer_id INTEGER, 
    project_name VARCHAR(50), 
    project_details TEXT,
    deadline DATE,
    status TEXT
);
'''

projects_list = '''CREATE TABLE IF NOT EXISTS projects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_full_name VARCHAR(100), 
    customer_id INTEGER,
    project_name VARCHAR(50), 
    project_details VARCHAR(50),
    deadline DATE,
    department VARCHAR(50),
    status TEXT
);
'''

project_students = """CREATE TABLE IF NOT EXISTS project_students (
    project_id INTEGER,
    student_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (student_id) REFERENCES staff(id)
);
"""


def create_table(conn):
    cur = conn.cursor()
    cur.execute(users_db)
    cur.execute(stuff_db)
    cur.execute(admin_db)
    cur.execute(projects_list)
    conn.commit()

def create_conn(path):
    conn = None
    try:
        conn = sqlite3.connect(path)
        print("Подключение к базе данных SQLite прошло успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")
    return conn


# def order(customer_full_name, project_name, project_detail):
#     with sqlite3.connect('db.sql') as conn:
#         cur = conn.cursor()
#         cur.execute("INSERT INTO project_queue(customer_full_name, project_name, project_details) VALUES(?, ?, ?)",
#                     (customer_full_name, project_name, project_detail))
#         conn.commit()


def add_stuff(full_name, id_project):
    with sqlite3.connect('db.sql') as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO staff (full_name, id_project, mistakes) VALUES(?, ?, ?)", (full_name, id_project, 0))
        conn.commit()
        cur.close()

#
# def approved_project():
#     with sqlite3.connect('db.sql') as conn:
#         cur = conn.cursor()
#         cur.execute('''
#             INSERT INTO staff(customer_full_name, taken_project, taken_project_details)
#             SELECT customer_full_name, project_name, project_details
#             FROM project_queue
#         ''')
#         conn.commit()


def delete_db(table, index):
    with sqlite3.connect('db.sql') as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table} WHERE id=?", (index,))
        conn.commit()
        cur.close()
        conn.close()
