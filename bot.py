import telebot
import schedule
import time
import threading
import os
import logging

# Настройки логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='bot.log', filemode='a')
logger = logging.getLogger(__name__)

# --- Настройки ---
API_TOKEN = '8151372161:AAFVYcCOTZ-Cs2grVb6qGovKQiVZZAVJrWM'  # Замените на ваш токен бота
ADMIN_IDS = [1882992222, 412411542]  # ID администраторов
phrases_file = 'cute_phrases.txt'
schedule_time_file = 'schedule_time.txt'
subscribers_file = 'subscribers.txt'
default_schedule_time = "14:01"
ADMIN_CHAT_ID = 1882992222  # ID чата администратора 

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

def load_subscribers():
    subscribers = {}
    if os.path.exists(subscribers_file):
        with open(subscribers_file, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                user_id, index = line.strip().split(',')
                subscribers[int(user_id)] = int(index)
    return subscribers

def save_subscribers():
    with open(subscribers_file, 'w', encoding='utf-8') as f:
        for user_id, index in subscribers.items():
            f.write(f"{user_id},{index}\n")

def send_cute_phrases():
    global cute_phrases
    cute_phrases = load_phrases()
    logger.info(f"Отправка милых фраз подписчикам. Количество фраз: {len(cute_phrases)}")

    if not cute_phrases:
        logger.warning("Список милых фраз пуст. Сообщения не будут отправлены.")
        return

    for subscriber, index in list(subscribers.items()):
        if index < len(cute_phrases):
            phrase = cute_phrases[index]
            try:
                bot.send_message(subscriber, phrase)
                subscribers[subscriber] += 1
                save_subscribers()  # Сохраняем подписчиков после успешной отправки
                logger.info(f"Фраза отправлена пользователю {subscriber}: {phrase}")
            except telebot.apihelper.ApiTelegramException as e:
                logger.error(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")
        else:
            try:
                bot.send_message(subscriber, "Милые фразы на сегодня закончились! Подпишись снова через /subscribe, чтобы получать новые фразы.")
                del subscribers[subscriber]
                save_subscribers()
                logger.info(f"Пользователь {subscriber} удален из подписчиков: фразы закончились.")
            except telebot.apihelper.ApiTelegramException as e:
                logger.error(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")

def send_admin_message(text):
    """Отправляет сообщение администратору."""
    try:
        bot.send_message(ADMIN_CHAT_ID, text)
        logger.info(f"Сообщение отправлено администратору: {text}")
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Ошибка отправки сообщения администратору: {e}")

def save_schedule_time():
    with open(schedule_time_file, 'w') as f:
        f.write(scheduled_time)
    logger.info(f"Новое время рассылки сохранено: {scheduled_time}")

# --- Инициализация ---
bot = telebot.TeleBot(API_TOKEN)
cute_phrases = load_phrases()
scheduled_time = load_schedule_time()
subscribers = load_subscribers()

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Ты подписался на рассылку милых фраз. Напиши /subscribe, чтобы получать их ежедневно.")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    if message.chat.id not in subscribers:
        subscribers[message.chat.id] = 0
        save_subscribers()
        bot.send_message(message.chat.id, "Поздравляю! Теперь ты будешь получать милые фразы каждый день.")
        send_admin_message(f"Новый подписчик: {message.chat.id}")
        logger.info(f"Пользователь {message.chat.id} подписался.")
    else:
        bot.send_message(message.chat.id, "Ты уже подписан на рассылку милых фраз.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    if message.chat.id in subscribers:
        del subscribers[message.chat.id]
        save_subscribers()
        bot.send_message(message.chat.id, "Ты отписался от рассылки милых фраз.")
        send_admin_message(f"Пользователь отписался: {message.chat.id}")
        logger.info(f"Пользователь {message.chat.id} отписался.")
    else:
        bot.send_message(message.chat.id, "Ты не подписан на рассылку милых фраз.")

@bot.message_handler(commands=['list_subscribers'], func=lambda message: is_admin(message.from_user.id))
def list_subscribers(message):
    """Выводит список подписчиков."""
    if subscribers:
        subscriber_list = "\n".join(f"ID: {user_id}, Последний индекс: {index}" for user_id, index in subscribers.items())
        bot.send_message(message.chat.id, f"Текущие подписчики:\n{subscriber_list}")
    else:
        bot.send_message(message.chat.id, "Список подписчиков пуст.")

@bot.message_handler(commands=['admin'], func=lambda message: is_admin(message.from_user.id))
def admin_panel(message):
    bot.send_message(message.chat.id, f"Текущее время рассылки: {scheduled_time}\n\nЧтобы изменить время, используйте команду /settime ЧЧ:ММ\n\n/sendall <время (ЧЧ:ММ)> <текст> - отправить сообщение всем подписчикам в указанное время.")

@bot.message_handler(commands=['settime'], func=lambda message: is_admin(message.from_user.id))
def set_schedule_time(message):
    global scheduled_time
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Пожалуйста, укажите время в формате ЧЧ:ММ.")
        return

    new_time = parts[1]
    try:
        time.strptime(new_time, "%H:%M")  # Проверка корректности формата времени
        scheduled_time = new_time
        save_schedule_time()  # Сохраняем новое время в файл
        bot.send_message(message.chat.id, f"Время рассылки успешно обновлено на {scheduled_time}.")
        
        # Дополнительно: очищаем старые задачи и перезапланируем новую
        schedule.clear()  # Очищаем все запланированные задачи
        schedule.every().day.at(scheduled_time).do(send_cute_phrases)  # Запланируем новую задачу для отправки
        logger.info(f"Запланировано новое время для отправки фраз: {scheduled_time}")
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный формат времени. Убедитесь, что вы используете формат ЧЧ:ММ.")

@bot.message_handler(commands=['sendall'], func=lambda message: is_admin(message.from_user.id))
def send_all_message(message):
    try:
        parts = message.text.split(None, 2)
        if len(parts) < 2:
            raise IndexError

        if len(parts) == 3:
            schedule_time = parts[1]
            text = parts[2]
            time.strptime(schedule_time, "%H:%M")

            # Запланировать отправку
            schedule.every().day.at(schedule_time).do(lambda t=text: send_bulk_message(t))
            bot.send_message(message.chat.id, f"Сообщение будет отправлено всем подписчикам в {schedule_time}.")
            logger.info(f"Запланировано отправка сообщения всем подписчикам в {schedule_time}.")
        else:
            text = parts[1]
            count = send_bulk_message(text)
            bot.send_message(message.chat.id, f"Сообщение успешно отправлено {count} подписчикам.")

        send_admin_message(f"Администратор отправил сообщение всем подписчикам: {text}")
    except (ValueError, IndexError) as e:
        bot.send_message(message.chat.id, "Используйте команду /sendall <время (ЧЧ:ММ)> <текст> для запланированной отправки или /sendall <текст> для немедленной отправки.")
        logger.error(f"Ошибка при попытке отправить сообщение: {e}")

def send_bulk_message(text):
    count = 0
    for subscriber in subscribers:
        try:
            bot.send_message(subscriber, text)
            count += 1
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")
    logger.info(f"Сообщения отправлено: {count} подписчикам")
    return count

@bot.message_handler(commands=['loadphrases'], func=lambda message: is_admin(message.from_user.id))
def load_new_phrases(message):
    global cute_phrases
    cute_phrases = load_phrases()
    bot.send_message(message.chat.id, f"Список фраз обновлен. Количество фраз: {len(cute_phrases)}")
    send_admin_message(f"Список фраз обновлен. Количество фраз: {len(cute_phrases)}")

@bot.message_handler(content_types=['document'], func=lambda message: is_admin(message.from_user.id))
def handle_document(message):
    if message.document.mime_type == 'text/plain':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(phrases_file, 'wb') as new_file:
            new_file.write(downloaded_file)

        global cute_phrases
        cute_phrases = load_phrases()  # Загружаем фразы сразу после сохранения
        bot.send_message(message.chat.id, f"Фразы успешно обновлены. Количество фраз: {len(cute_phrases)}")
        send_admin_message("Новый список фраз был загружен.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, загрузите текстовый файл с фразами.")

@bot.message_handler(commands=['listphrases'], func=lambda message: is_admin(message.from_user.id))
def list_phrases(message):
    if cute_phrases:
        phrase_list = "\n".join(cute_phrases)
        bot.send_message(message.chat.id, f"Текущие фразы:\n{phrase_list}")
    else:
        bot.send_message(message.chat.id, "Список фраз пуст.")

@bot.message_handler(content_types=['photo'], func=lambda message: is_admin(message.from_user.id))
def handle_photo(message):
    """Обрабатываем загруженные изображения от администратора и запрашиваем текст."""
    global sent_image_id
    sent_image_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "Теперь введите текст для отправки всем подписчикам.")
    bot.register_next_step_handler(message, send_photo_message)

def send_photo_message(message):
    """Отправляет фото и текст всем подписчикам."""
    text = message.text
    if not text:
        bot.send_message(message.chat.id, "Пожалуйста, введите текст, который хотите отправить вместе с фото.")
        return

    count = 0
    for subscriber in subscribers:
        try:
            bot.send_photo(subscriber, sent_image_id, caption=text)
            count += 1
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Ошибка отправки сообщения пользователю {subscriber}: {e}")

    bot.send_message(message.chat.id, f"Фото и сообщение успешно отправлены {count} подписчикам.")

# --- Планировщик ---
def run_schedule():
    logger.info("Запуск планировщика...")
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- Запуск ---
if __name__ == "__main__":
    threading.Thread(target=run_schedule, daemon=True).start()
    logger.info("Бот запущен и ожидает команд...")
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        logger.error(f"Ошибка при запущенном боте: {e}")