# # import psutil
# import telebot
# from admin.configE import STAFF, Bot_MAIN
# # from staff import menu, bot_token as bot_s
# # from user import start, bot_token as bot_u
#
# # Проверяем, запущены ли другие процессы с таким же именем
# # def check_running_processes():
# #     current_process = psutil.Process()
# #     for process in psutil.process_iter(['pid', 'name']):
# #         if process.info['name'] == current_process.name() and process.info['pid'] != current_process.pid:
# #             return True
# #     return False
#
# # Если другие процессы уже запущены, выводим сообщение и завершаем текущий процесс
# # if check_running_processes():
# #     print("Another instance of the bot is already running.")
# #     exit()
#
# bot = telebot.TeleBot(Bot_MAIN)
#
# bot_s = bot
# bot_u = bot
#
#
# @bot.message_handler(commands=['start'])
# def main_start(message):
#     bot.send_message(message.chat.id, 'Hello')
#     if message.from_user.id in STAFF:
#         menu(message)  # Предполагается, что функция menu определена в модуле staff
#         bot.send_message(message.chat.id, 'Hello Staff')
#         bot.stop_polling()
#     else:
#         start(message)
#         bot.send_message(message.chat.id, f'Hello {message.from_user.first_name} {message.from_user.last_name}')
#         bot.stop_polling()
#
#
# # Запуск бота
# bot.polling()
