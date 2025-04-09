import telebot
import schedule
import time
import threading
import os

# --- Настройки ---
API_TOKEN = '8151372161:AAFVYcCOTZ-Cs2grVb6qGovKQiVZZAVJrWM'  # Ваш токен бота
ADMIN_ID = 1882992222  # Установите ID администратора
phrases_file = 'cute_phrases.txt'
schedule_time_file = 'schedule_time.txt'
default_schedule_time = "14:01"
ADMIN_CHAT_ID = 1882992222 # Установите ID чата администратора (можно совпадать с ADMIN_ID)


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

@bot.message_handler(commands=['admin'], func=lambda message: message.from_user.id == ADMIN_ID)
def admin_panel(message):
    bot.send_message(message.chat.id,
                     f"Текущее время рассылки: {scheduled_time}\n\nЧтобы изменить время, используйте команду /settime ЧЧ:ММ\n\n/sendall <текст> - отправить сообщение всем подписчикам.")

@bot.message_handler(commands=['settime'], func=lambda message: message.from_user.id == ADMIN_ID)
def set_schedule_time(message):
    global scheduled_time
    try:
        new_time = message.text.split()[1]
        time.strptime(new_time, "%H:%M")  # Проверка формата времени
        scheduled_time = new_time
        save_schedule_time(scheduled_time)
        schedule.clear()
        schedule.every().day.at(scheduled_time).do(send_cute_phrases)
        bot.send_message(message.chat.id, f"Время рассылки установлено на {scheduled_time}")
        send_admin_message(f"Время рассылки изменено на: {scheduled_time}")
    except (ValueError, IndexError):
        bot.send_message(message.chat.id, "Неверный формат времени. Используйте ЧЧ:ММ (например, 10:30)")

@bot.message_handler(commands=['sendall'], func=lambda message: message.from_user.id == ADMIN_ID)
def send_all_message(message):
    try:
        text = message.text.split(None, 1)[1]  # Получаем текст после /sendall
        count = 0
        for subscriber in subscribers:
            try:
                bot.send_message(subscriber, text)
                count += 1
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")
        bot.send_message(message.chat.id, f"Сообщение успешно отправлено {count} подписчикам.")
        send_admin_message(f"Администратор отправил сообщение всем подписчикам: {text}")
    except IndexError:
        bot.send_message(message.chat.id, "Используйте команду /sendall <текст> для отправки сообщения.")


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