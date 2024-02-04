import sqlite3
from sqlite3 import Error
ADMINS = [975713395]
STAFF = []

about_c = 'Отдел Commerce представляет собой динамичное и инновационное пространство, где студенты сосредотачивают свое внимание на изучении и понимании мира бизнеса и торговли. В рамках этого отдела студенты получают углубленные знания в области маркетинга, финансов, управления и экономики. Программа включает в себя не только теоретические аспекты, но и практические навыки, позволяя студентам применять свои знания на практике. Преподаватели отдела Commerce активно вовлечены в индустрию, обеспечивая актуальность учебного материала. Студенты отдела Commerce готовы к вызовам современного бизнес-мира, обладая широкими компетенциями и пониманием ключевых аспектов коммерции.'
about_e = 'Отдел Education представляет собой интеллектуальное и творческое сообщество, где студенты посвящают себя образованию и развитию. Здесь акцент делается на формировании критического мышления, исследовательских навыков и педагогической компетентности. Программа отдела Education охватывает различные аспекты образовательного процесса, включая психологию обучения, методику преподавания и вопросы современного образования. Студенты изучают инновационные методики и технологии обучения, готовясь к роли преподавателей и лидеров в образовательной области. Преподаватели отдела Education поддерживают атмосферу вдохновения и поощряют студентов к поиску новых идей для улучшения образовательной практики. Студенты отдела Education стремятся к тому, чтобы сделать значимый вклад в будущее образования.'
about_d = """Отдел Digital является инновационным и технологически ориентированным сообществом, где студенты глубоко погружаются в мир цифровых технологий и информационных наук. Здесь осуществляется синтез теоретических знаний и практических навыков в области программирования, разработки программного обеспечения, анализа данных и кибербезопасности. Программа отдела Digital ставит своей целью подготовку высококвалифицированных специалистов, способных решать сложные задачи в цифровой среде.
Студенты изучают современные языки программирования, методы обработки данных, искусственный интеллект, веб-разработку и другие актуальные темы. Отдел Digital также акцентирует внимание на творческом подходе к использованию технологий для решения бизнес-задач и создания инновационных проектов. Студенты развивают свои навыки в коллективных проектах, под руководством опытных преподавателей, и имеют возможность участвовать в стажировках в ведущих компаниях в сфере IT. Отдел Digital создает атмосферу, в которой поощряется креативность, предпринимательство и стремление к новым высотам в цифровой сфере.
"""

def create_conn(path):
    conn = None
    try:
        conn = sqlite3.connect(path)
        print("Подключение к базе данных SQLite прошло успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")
    return conn

def execute_query(conn, query):
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
        print("Запрос выполнен успешно")
    except Error as e:
        print(f"Произошла ошибка '{e}'")

def execute_read_query(conn, query):
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Произошла ошибка '{e}'")

def check_ad(message):
    global ADMINS
    return message.from_user.id in ADMINS

def chek_st(message):
    global STAFF
    return message.from_user.id in STAFF

def check_us(message):
    global ADMINS
    global STAFF
    return message.from_user.id not in ADMINS and STAFF

users_table = """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    user_name TEXT,
    surname TEXT,
    department TEXT,
    project TEXT
);
"""

projects_table = """CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    project_name TEXT,
    about TEXT,
    deadline DATE,
    department TEXT
);
"""

departments_table = """CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    department_name TEXT,
    project_id INTEGER,
    about TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
"""

project_students = """CREATE TABLE IF NOT EXISTS project_students (
    project_id INTEGER,
    student_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
);
"""

# order = """CREATE TABLE IF NOT EXISTS order (
#     id INTEGER PRIMARY KEY,
#     order_name TEXT,
#     about TEXT,
#     deadline DATE,
#     department TEXT,
#     orderer INTEGER
# );
# """

# Ваши запросы на вставку данных
create_users = """
INSERT INTO
  users (user_name, surname, department, project)
VALUES
  ('Джеймс','Мориарти', 'Commerce', 'tel' ),
  ('Лейла','Дик', 'Commerce', 'tel'),
  ('Бриджит','Камм', 'Education', 'edu'),
  ('Майк', 'Смит', 'Digital', 'dig'),
  ('Элизабет',' Вторая', 'Digital', 'dig'),
  ('Алымбек', 'Что-тотамов', 'Education', 'edu');
"""

create_projects = """
INSERT INTO
  projects (project_name, about, deadline, department)
VALUES
  ('tel', 'sell Phone', '2024-02-01', 'Commerce'),
  ('edu', 'sell clothes', '2024-03-15', 'Education'),
  ('dig', 'sell edu', '2024-04-30', 'Digital');
"""

create_project_students = """
INSERT INTO
  project_students (project_id, student_id)
VALUES
  (1, 1),
  (1, 2),
  (2, 4),
  (2, 5),
  (3, 3),
  (3, 6);
"""

create_departments = f"""
INSERT INTO
  departments (department_name, project_id, about)
VALUES
  ('Commerce', 1, '{about_c}'),
  ('Education', 2, '{about_e}'),
  ('Digital', 3, '{about_d}');
"""




"""
def list_tables(conn):
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = execute_read_query(conn, query)
    print("Tables in the database:")
    for table in tables:
        print(table[0])
# Создаем соединение
conn = create_conn('students.sql')
# Выводим список таблиц
list_tables(conn)
# Закрываем соединение
conn.close()

db_path = 'students.sql'

# Ваш SQL-запрос
check_table_query = """
#SELECT name FROM sqlite_master WHERE type='table' AND name='projects';
"""


# Подключение к базе данных и выполнение запроса
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(check_table_query)

# Получение результата
table_exists = cursor.fetchone() is not None

# Вывод результата
if table_exists:
    print("Таблица 'projects' успешно создана")

else:
    print("Таблица 'projects' не найдена")
select_projects_info = "PRAGMA table_info(projects);"
select_projects_info2 = "PRAGMA table_info(users);"
select_projects_info3 = "PRAGMA table_info(departments);"

projects_info = execute_read_query(conn, select_projects_info)
projects_info2 = execute_read_query(conn, select_projects_info2)
projects_info3 = execute_read_query(conn, select_projects_info3)

for column_info in projects_info:
    print(column_info)
for column_info in projects_info2:
    print(column_info)
for column_info in projects_info3:
    print(column_info)
# Закрываем соединение
cursor.close()
conn.close()
create_conn = create_conn('students.sql')
try:
    execute_query(create_conn, projects_table)
    print("Таблица 'projects' успешно создана")
except Exception as e:
    print(f"Ошибка при создании таблицы 'projects': {e}")
finally:
    create_conn.close()"""