import telebot
from telebot import types
from admin.configE import STAFF
from database import create_table, add_stuff, delete_db
from database import temp_proj_db, users_db, stuff_db, admin_db, project_students, projects_list
from database import create_conn
from admin.configE import Bot_MAIN

bot = telebot.TeleBot(Bot_MAIN)
user_data_dict = {}


@bot.message_handler(commands=['start'])
def menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("List of staff", callback_data='staff_list'))
    markup.add(types.InlineKeyboardButton("Register as staff", callback_data='staff_register'))
    markup.add(types.InlineKeyboardButton("Staff account", callback_data='staff_account'))
    markup.add(types.InlineKeyboardButton("Open website", url='https://example.com'))
    bot.send_message(message.chat.id, 'Menu:', reply_markup=markup)


# @bot.message_handler(commands=['register'])
def register(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Register as staff", callback_data='staff_register'))
    bot.send_message(message.chat.id, "Choose:", reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: callback.data == 'staff_register')
def staff_register(callback):
    chat_id = callback.message.chat.id
    user_data_dict.setdefault(chat_id, {})
    bot.send_message(chat_id, 'Great! You selected in group. Enter your name:')
    user_data_dict[chat_id]['group'] = 'staff'
    bot.register_next_step_handler_by_chat_id(chat_id, user_name)

def user_name(message):
    chat_id = message.chat.id
    name = message.text.strip()
    user_data_dict[chat_id]['name'] = name
    bot.send_message(chat_id, "Enter password")
    bot.register_next_step_handler(message, user_password)

def user_password(message):
    chat_id = message.chat.id
    password = message.text.strip()

    if chat_id not in user_data_dict or 'name' not in user_data_dict[chat_id]:
        bot.send_message(chat_id, "Please register first.")
        return

    user_data_dict[chat_id]['password'] = password
    save_user_data(chat_id)

def save_user_data(chat_id):
    if chat_id not in user_data_dict or 'name' not in user_data_dict[chat_id] or 'password' not in user_data_dict[chat_id]:
        bot.send_message(chat_id, "Please complete the registration first.")
        return


    name = user_data_dict[chat_id]['name']
    password = user_data_dict[chat_id]['password']

    add_stuff(name, 0)

    markup = types.InlineKeyboardMarkup()
    bot.send_message(chat_id,
                     f"You are registered in staff! "
                     f"\nName: {name}",
                     reply_markup=markup)

    user_data_dict[chat_id].clear()

def show_pending_order(chat_id):
    conn = create_conn('db.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM projects')
    orders = cur.fetchall()
    markup = types.InlineKeyboardMarkup()
    for i, order in enumerate(orders, start=1):
        markup.add(types.InlineKeyboardButton(f"Order{i}", callback_data=f'order_{order[0]}'))
    cur.close()
    conn.close()
    bot.send_message(chat_id, "List of orders:", reply_markup=markup)

def show_order_info(chat_id, order_id):
    conn = create_conn('db.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM projects WHERE id = ?', (order_id,))
    order = cur.fetchone()
    cur.close()
    conn.close()

    if order:
        info_message = (f"Order information:\nOrder ID: {order[0]}\n"
                        f"User ID: {order[1]}\n"
                        f"Description: {order[2]}\n"
                        f"Status: {order[3]}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("Accept", callback_data=''))
        markup.add(types.InlineKeyboardButton("Cancel", callback_data=''))
        bot.send_message(chat_id, info_message, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Order not found.")


# def hash_password(password):
#     hashed_password = hashlib.sha256(password.encode()).hexdigest()
#     return hashed_password


# # @bot.message_handler(commands=['login'])
# def login(message):
#     markup = types.InlineKeyboardMarkup(row_width=2)
#     markup.add(types.InlineKeyboardButton("Login as staff", callback_data='staff_login'))
#     bot.send_message(message.chat.id, "Choose:", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == 'staff_login')
def staff_login(callback):
    chat_id = callback.message.chat.id
    bot.send_message(chat_id, 'Enter your name:')
    bot.register_next_step_handler_by_chat_id(chat_id, check_staff_login)


def check_staff_login(message):
    chat_id = message.chat.id
    name = message.text.strip()

    conn = create_conn('db.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM staff WHERE full_name = ?', (name,))
    user = cur.fetchone()
    print(user)

    cur.close()
    conn.close()

    if user:
        bot.send_message(chat_id, "Enter your password:")
        user_data_dict[chat_id] = {'name': name}
        bot.register_next_step_handler(message, check_staff_password)
    else:
        bot.send_message(chat_id, "User not found. Please register or check your name.")


def check_staff_password(message):
    chat_id = message.chat.id
    name = user_data_dict[chat_id]['name']
    password = message.text.strip()

    conn = create_conn('db.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM staff WHERE full_name = ?', (name,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("Your account", callback_data='your_staff_account'))
        bot.send_message(chat_id, f"Welcome back, {name}!", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Incorrect password. Please try again or register.")
        user_data_dict[chat_id] = {}


def staff_account(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("My Info", callback_data='my_info'))
    markup.add(types.InlineKeyboardButton("Your - Pending order", callback_data='pending_orders'))
    markup.add(types.InlineKeyboardButton("Your - Completed order", callback_data='completed_orders'))
    bot.send_message(message.chat.id, 'Your menu:', reply_markup=markup)


def my_info(message):
    chat_id = message.chat.id
    conn = create_conn('db.sql')
    cur = conn.cursor()

    if chat_id in user_data_dict and 'name' in user_data_dict[chat_id]:
        name = user_data_dict[chat_id]['name']
        cur.execute('SELECT * FROM staff WHERE full_name = ?', (name,))
        user = cur.fetchone()

        if user:
            order_id = user[3] if len(user) > 3 else None
            if order_id is not None:
                cur.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
                order = cur.fetchone()
                if order:
                    info_message = (f"Staff information:\nName: {user[1]}\n"
                                    f"Order: \nOrder ID: {order[0]}\n"
                                    f"Description: {order[2]}\n"
                                    f"Status: {order[3]}")
                    bot.send_message(chat_id, info_message)
                else:
                    bot.send_message(chat_id, "Order not found.")
            else:
                info_message = f"Staff information:\nName: {user[1]}\nOrder: None"
                bot.send_message(chat_id, info_message)
        else:
            bot.send_message(chat_id, "User not found.")
    else:
        bot.send_message(chat_id, "Please log in first.")

    cur.close()
    conn.close()


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    message = callback.message
    chat_id = callback.message.chat.id
    if callback.data == 'staff_account':
        staff_login(callback)
    elif callback.data == 'your_staff_account':
        staff_account(message)
    elif callback.data.startswith('order'):
        order_id = int(callback.data.split('_')[1])
        show_order_info(callback.message.chat.id, order_id)
    elif callback.data == 'my_info':
        my_info(callback.message)
    elif callback.data == 'pending_orders':
        show_pending_order(chat_id)
    elif callback.data == 'completed_orders':
        pass
    elif callback.data == 'accept_order':
        pass
    elif callback.data == 'cancel_order':
        pass


bot.polling(none_stop=True)