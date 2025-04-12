import telebot
import schedule
import time
import threading
import os

# --- Настройки ---
API_TOKEN = '8151372161:AAFVYcCOTZ-Cs2grVb6qGovKQiVZZAVJrWM'  # Ваш токен бота
ADMIN_IDS = [1882992222, 412411542] 
phrases_file = 'cute_phrases.txt'
schedule_time_file = 'schedule_time.txt'
default_schedule_time = "14:01"
ADMIN_CHAT_ID = 1882992222 # Установите ID чата администратора (можно совпадать с ADMIN_ID)


# Проверка, является ли пользователь администратором
def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- Функции ---
def load_phrases():
    if os.path.exists(phrases_file):
        with open(phrases_file, 'r', encoding='utf-8') as file:
            return file.read().splitlines()
    return []

def load_schedule_time():
    if os.path.exists(schedule_time_file):
        with open(schedule_time_file, 'r') as f:
            return f.read().strip()
    return default_schedule_time

def save_schedule_time(time_str):
    with open(schedule_time_file, 'w') as f:
        f.write(time_str)

def send_cute_phrases():
    global cute_phrases  # Объявляем, что используем глобальную переменную
    cute_phrases = load_phrases()  # Перезагружаем фразы перед отправкой

    for subscriber, index in list(subscribers.items()):
        if index < len(cute_phrases):
            phrase = cute_phrases[index]
            try:
                bot.send_message(subscriber, phrase)
                subscribers[subscriber] += 1
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")
                # Здесь можно добавить обработку ошибок, например, удаление пользователя из списка, если он заблокировал бота
        else:
            try:
                bot.send_message(subscriber, "Милые фразы на сегодня закончились! Подпишись снова через /subscribe, чтобы получать новые фразы.")
                del subscribers[subscriber]
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")

def send_admin_message(text):
    """Отправляет сообщение администратору."""
    try:
        bot.send_message(ADMIN_CHAT_ID, text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Ошибка отправки сообщения администратору: {e}")


# --- Инициализация ---
bot = telebot.TeleBot(API_TOKEN)
cute_phrases = load_phrases()
scheduled_time = load_schedule_time()
subscribers = {}


# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Ты подписался на рассылку милых фраз. Напиши /subscribe, чтобы получать их ежедневно.")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    if message.chat.id not in subscribers:
        subscribers[message.chat.id] = 0
        bot.send_message(message.chat.id, "Поздравляю! Теперь ты будешь получать милые фразы каждый день.")
        send_admin_message(f"Новый подписчик: {message.chat.id}")
    else:
        bot.send_message(message.chat.id, "Ты уже подписан на рассылку милых фраз.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    if message.chat.id in subscribers:
        del subscribers[message.chat.id]
        bot.send_message(message.chat.id, "Ты отписался от рассылки милых фраз.")
        send_admin_message(f"Пользователь отписался: {message.chat.id}")
    else:
        bot.send_message(message.chat.id, "Ты не подписан на рассылку милых фраз.")

# --- Обработчики команд ---
@bot.message_handler(commands=['admin'], func=lambda message: is_admin(message.from_user.id))
def admin_panel(message):
    bot.send_message(message.chat.id,
                     f"Текущее время рассылки: {scheduled_time}\n\nЧтобы изменить время, используйте команду /settime ЧЧ:ММ\n\n/sendall <время> <текст> - отправить сообщение всем подписчикам в указанное время.")

@bot.message_handler(commands=['sendall'], func=lambda message: is_admin(message.from_user.id))
def send_all_message(message):
    try:
        parts = message.text.split(None, 2)  # Разделяем на части
        if len(parts) < 2:
            raise IndexError
        
        # Если указан только текст, отправляем сразу, иначе планируем
        if len(parts) == 3:
            schedule_time = parts[1]
            text = parts[2]
            time.strptime(schedule_time, "%H:%M")  # Проверка формата времени
            schedule.every().day.at(schedule_time).do(lambda: send_bulk_message(text))
            bot.send_message(message.chat.id, f"Сообщение будет отправлено всем подписчикам в {schedule_time}.")
        else:
            text = parts[1]
            count = send_bulk_message(text)
            bot.send_message(message.chat.id, f"Сообщение успешно отправлено {count} подписчикам.")
        
        send_admin_message(f"Администратор отправил сообщение всем подписчикам: {text}")
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "Используйте команду /sendall <время (ЧЧ:ММ)> <текст> для запланированной отправки или /sendall <текст> для немедленной отправки.")

def send_bulk_message(text):
    count = 0
    for subscriber in subscribers:
        try:
            bot.send_message(subscriber, text)
            count += 1
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")
    return count


@bot.message_handler(commands=['loadphrases'], func=lambda message: message.from_user.id == ADMIN_ID)
def load_new_phrases(message):
    global cute_phrases
    cute_phrases = load_phrases()
    bot.send_message(message.chat.id, f"Список фраз обновлен. Количество фраз: {len(cute_phrases)}")
    send_admin_message(f"Список фраз обновлен. Количество фраз: {len(cute_phrases)}")



# --- Планировщик ---
def run_schedule():
    schedule.every().day.at(scheduled_time).do(send_cute_phrases)
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- Запуск ---
if __name__ == "__main__":
    threading.Thread(target=run_schedule, daemon=True).start()  # Запуск в фоновом режиме
    bot.polling(non_stop=True)  # Используйте non_stop для устойчивой работы