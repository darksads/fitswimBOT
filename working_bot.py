"""
РАБОЧИЙ БОТ ДЛЯ ПЛАВАНИЯ - FITSWIM AI ПОМОЩНИК
"""

import logging
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ТОКЕН БОТА
BOT_TOKEN = "8550408293:AAFeyT1kA8jOA-7-Ubr8JJPawu4hgXYm2Q4"

# Состояния для ConversationHandler
CHOOSING_DAY, CHOOSING_TIME = range(2)

# Глобальные переменные
user_trainings = {}
user_reminders = {}

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем клавиатуру
    keyboard = [
        [KeyboardButton("🏊 Записать тренировку")],
        [KeyboardButton("📊 Моя статистика")],
        [KeyboardButton("💡 Совет по плаванию")],
        [KeyboardButton("🎯 Поставить цель"), KeyboardButton("🔔 Мои напоминания")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"🏊‍♂️ Привет, {user.first_name}!\n\n"
        f"Я твой AI помощник FitSwim!\n"
        f"Используй кнопки ниже:",
        reply_markup=reply_markup
    )
    
    logger.info(f"Пользователь {user.id} запустил бота")

# Обработка кнопки "📊 Моя статистика"
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику пользователя"""
    user_id = update.effective_user.id
    
    if user_id in user_trainings and user_trainings[user_id]:
        total_trainings = len(user_trainings[user_id])
        total_time = sum(user_trainings[user_id])
        total_calories = total_time * 10
        avg_time = total_time // total_trainings
        
        stats_text = f"""
📊 *Твоя статистика:*

🏊 Всего тренировок: {total_trainings}
⏱️ Общее время: {total_time} минут
🔥 Сожжено калорий: ~{total_calories}
📈 Среднее время: {avg_time} минут

🎯 *Прогресс:*
"""
        if total_trainings < 5:
            stats_text += "Ты только начинаешь! Первые 10 тренировок - самые важные! 🏊‍♂️"
        elif total_trainings < 20:
            stats_text += "Отличный старт! Продолжай в том же духе! 💪"
        else:
            stats_text += "Потрясающе! Ты настоящий пловец! 🏆"
    else:
        stats_text = "У тебя пока нет записанных тренировок.\nНачни с кнопки '🏊 Записать тренировку'!"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# Обработка кнопки "🔔 Мои напоминания"
async def show_reminders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню напоминаний"""
    user_id = update.effective_user.id
    
    # Проверяем есть ли напоминания
    has_reminders = user_id in user_reminders and user_reminders[user_id]
    active_count = 0
    
    if has_reminders:
        active_reminders = [r for r in user_reminders[user_id] if r.get('active', True)]
        active_count = len(active_reminders)
    
    # Создаем текст в зависимости от наличия напоминаний
    if has_reminders and active_count > 0:
        text = f"🔔 *У тебя {active_count} активных напоминаний*\n\nЧто хочешь сделать?"
    else:
        text = "🔔 *У тебя пока нет напоминаний*\n\nХочешь установить первое напоминание?"
    
    # Создаем инлайн-кнопки
    inline_keyboard = [
        [InlineKeyboardButton("➕ Установить напоминание", callback_data="start_reminder")],
        [InlineKeyboardButton("📋 Посмотреть мои напоминания", callback_data="show_my_reminders")],
        [InlineKeyboardButton("🗑️ Удалить все напоминания", callback_data="delete_all_reminders")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# Начать установку напоминания
async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс установки напоминания"""
    query = update.callback_query
    await query.answer()
    
    # Создаем клавиатуру для выбора дня
    keyboard = [
        [
            InlineKeyboardButton("Сегодня", callback_data="day_today"),
            InlineKeyboardButton("Завтра", callback_data="day_tomorrow")
        ],
        [
            InlineKeyboardButton("Пн", callback_data="day_monday"),
            InlineKeyboardButton("Вт", callback_data="day_tuesday"),
            InlineKeyboardButton("Ср", callback_data="day_wednesday"),
            InlineKeyboardButton("Чт", callback_data="day_thursday"),
            InlineKeyboardButton("Пт", callback_data="day_friday")
        ],
        [
            InlineKeyboardButton("Сб", callback_data="day_saturday"),
            InlineKeyboardButton("Вс", callback_data="day_sunday")
        ],
        [InlineKeyboardButton("📝 Ввести свою дату", callback_data="day_custom")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📅 *Выбери день для напоминания:*\n\n"
        "Или нажми 'Ввести свою дату' чтобы указать конкретную дату",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return CHOOSING_DAY

# Показать мои напоминания
async def show_my_reminders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает все напоминания пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id in user_reminders and user_reminders[user_id]:
        reminders_list = user_reminders[user_id]
        active_reminders = [r for r in reminders_list if r.get('active', True)]
        
        if active_reminders:
            text = "📋 *Твои активные напоминания:*\n\n"
            for i, reminder in enumerate(active_reminders, 1):
                text += f"{i}. {reminder['day'].capitalize()} в {reminder['time']}\n"
            
            text += f"\nВсего: {len(active_reminders)} напоминаний"
        else:
            text = "У тебя пока нет активных напоминаний."
    else:
        text = "У тебя пока нет напоминаний."
    
    # Добавляем кнопки для возврата
    inline_keyboard = [
        [InlineKeyboardButton("➕ Добавить напоминание", callback_data="start_reminder")],
        [InlineKeyboardButton("🔙 Назад к меню", callback_data="back_to_reminders_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# Назад к меню напоминаний
async def back_to_reminders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает к меню напоминаний"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Проверяем есть ли напоминания
    has_reminders = user_id in user_reminders and user_reminders[user_id]
    active_count = 0
    
    if has_reminders:
        active_reminders = [r for r in user_reminders[user_id] if r.get('active', True)]
        active_count = len(active_reminders)
    
    # Создаем текст в зависимости от наличия напоминаний
    if has_reminders and active_count > 0:
        text = f"🔔 *У тебя {active_count} активных напоминаний*\n\nЧто хочешь сделать?"
    else:
        text = "🔔 *У тебя пока нет напоминаний*\n\nХочешь установить первое напоминание?"
    
    # Создаем инлайн-кнопки
    inline_keyboard = [
        [InlineKeyboardButton("➕ Установить напоминание", callback_data="start_reminder")],
        [InlineKeyboardButton("📋 Посмотреть мои напоминания", callback_data="show_my_reminders")],
        [InlineKeyboardButton("🗑️ Удалить все напоминания", callback_data="delete_all_reminders")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# Обработка выбора дня
async def choose_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор дня"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "day_custom":
        await query.edit_message_text(
            "📝 *Введи дату в формате ДД.ММ*\n\n"
            "Например: 15.01 или 20.12\n\n"
            "Или напиши 'отмена' для отмены",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_custom_date'] = True
        context.user_data['user_id'] = user_id
        return CHOOSING_DAY
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Установка напоминания отменена.")
        return ConversationHandler.END
    
    # Сохраняем выбранный день
    day_mapping = {
        "day_today": "сегодня",
        "day_tomorrow": "завтра",
        "day_monday": "понедельник",
        "day_tuesday": "вторник",
        "day_wednesday": "среда",
        "day_thursday": "четверг",
        "day_friday": "пятница",
        "day_saturday": "суббота",
        "day_sunday": "воскресенье"
    }
    
    selected_day = day_mapping.get(query.data, "сегодня")
    context.user_data['reminder_day'] = selected_day
    context.user_data['user_id'] = user_id
    
    # Переходим к выбору времени
    await choose_time_step(query, context)
    return CHOOSING_TIME

# Шаг выбора времени
async def choose_time_step(query, context):
    """Показывает клавиатуру для выбора времени"""
    # Создаем клавиатуру с временем
    keyboard = []
    
    # Часы с интервалом в 1 час
    times = []
    for hour in range(7, 23):  # с 7 утра до 22 вечера
        times.extend([f"{hour:02d}:00", f"{hour:02d}:30"])
    
    # Разбиваем на ряды по 4 кнопки
    for i in range(0, len(times), 4):
        row = []
        for time in times[i:i+4]:
            row.append(InlineKeyboardButton(time, callback_data=f"time_{time}"))
        keyboard.append(row)
    
    # Добавляем кнопку для ввода своего времени
    keyboard.append([InlineKeyboardButton("📝 Ввести свое время", callback_data="time_custom")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📅 День: *{context.user_data['reminder_day'].capitalize()}*\n\n"
        f"⏰ *Выбери время тренировки:*\n"
        f"Или нажми 'Ввести свое время'",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Обработка выбора времени
async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор времени"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "time_custom":
        await query.edit_message_text(
            "⏰ *Введи время в формате ЧЧ:ММ*\n\n"
            "Например: 18:30 или 09:15\n\n"
            "Или напиши 'отмена' для отмены",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_custom_time'] = True
        return CHOOSING_TIME
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Установка напоминания отменена.")
        return ConversationHandler.END
    
    # Получаем выбранное время
    selected_time = query.data.replace("time_", "")
    
    # Сохраняем напоминание
    user_id = context.user_data['user_id']
    day = context.user_data['reminder_day']
    
    await save_reminder(user_id, day, selected_time, context, query)

# Сохранение напоминания
async def save_reminder(user_id, day, time_str, context, query=None):
    """Сохраняет напоминание и планирует уведомление"""
    # Сохраняем в глобальный словарь
    if user_id not in user_reminders:
        user_reminders[user_id] = []
    
    reminder = {
        'day': day,
        'time': time_str,
        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'active': True
    }
    
    user_reminders[user_id].append(reminder)
    
    # Планируем напоминание
    success = await schedule_reminder(user_id, day, time_str, context)
    
    if success:
        message = (
            f"✅ *Напоминание установлено!*\n\n"
            f"📅 День: {day.capitalize()}\n"
            f"⏰ Время: {time_str}\n\n"
            f"Я напомню тебе о тренировке! 💪\n\n"
            f"Всего активных напоминаний: {len([r for r in user_reminders[user_id] if r['active']])}"
        )
    else:
        message = (
            f"⚠️ *Напоминание сохранено, но есть проблема с планированием*\n\n"
            f"📅 День: {day.capitalize()}\n"
            f"⏰ Время: {time_str}\n\n"
            f"Я сохраню напоминание, но уведомление может не прийти."
        )
    
    if query:
        await query.edit_message_text(message, parse_mode='Markdown')
    else:
        # Если нет query (пользователь ввел время текстом)
        user_data = context.user_data
        if 'last_message_id' in user_data:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=user_data['last_message_id'],
                    text=message,
                    parse_mode='Markdown'
                )
            except:
                pass
    
    # Очищаем данные
    if 'reminder_day' in context.user_data:
        del context.user_data['reminder_day']
    if 'user_id' in context.user_data:
        del context.user_data['user_id']
    if 'waiting_for_custom_time' in context.user_data:
        del context.user_data['waiting_for_custom_time']
    if 'waiting_for_custom_date' in context.user_data:
        del context.user_data['waiting_for_custom_date']
    
    return ConversationHandler.END

# Планирование напоминания
async def schedule_reminder(user_id, day_str, time_str, context):
    """Планирует отправку напоминания"""
    try:
        now = datetime.now()
        hour, minute = map(int, time_str.split(':'))
        
        # Определяем дату напоминания
        if day_str == "сегодня":
            reminder_date = now.date()
        elif day_str == "завтра":
            reminder_date = (now + timedelta(days=1)).date()
        elif day_str in ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]:
            # День недели
            days_map = {
                "понедельник": 0, "вторник": 1, "среда": 2,
                "четверг": 3, "пятница": 4, "суббота": 5, "воскресенье": 6
            }
            target_day = days_map[day_str]
            current_day = now.weekday()
            
            days_ahead = target_day - current_day
            if days_ahead < 0:
                days_ahead += 7
            
            reminder_date = (now + timedelta(days=days_ahead)).date()
        else:
            # Пытаемся распарсить дату из формата ДД.ММ
            try:
                day, month = map(int, day_str.split('.'))
                current_year = now.year
                reminder_date = datetime(current_year, month, day).date()
                
                # Если дата уже прошла в этом году, берем следующий год
                if reminder_date < now.date():
                    reminder_date = datetime(current_year + 1, month, day).date()
            except:
                # Если не удалось, используем сегодня
                reminder_date = now.date()
        
        # Создаем полный datetime
        reminder_datetime = datetime.combine(reminder_date, datetime.min.time()).replace(
            hour=hour, minute=minute
        )
        
        # Если время уже прошло, переносим
        if reminder_datetime < now:
            if day_str in ["сегодня", "завтра"] or '.' in day_str:
                reminder_datetime += timedelta(days=1)
            elif day_str in ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]:
                reminder_datetime += timedelta(days=7)
        
        # Вычисляем задержку в секундах
        delay_seconds = (reminder_datetime - now).total_seconds()
        
        if delay_seconds > 0:
            # Создаем уникальное имя для задачи
            job_name = f"reminder_{user_id}_{int(reminder_datetime.timestamp())}"
            
            # Добавляем задачу в JobQueue
            context.job_queue.run_once(
                callback=send_reminder_callback,
                when=delay_seconds,
                data={
                    'user_id': user_id,
                    'day': day_str,
                    'time': time_str
                },
                name=job_name
            )
            
            logger.info(f"Напоминание запланировано для {user_id} на {reminder_datetime}")
            return True
        else:
            logger.warning(f"Напоминание уже просрочено для {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка планирования напоминания: {e}")
        return False

# Callback для отправки напоминания
async def send_reminder_callback(context):
    """Отправляет напоминание пользователю"""
    job = context.job
    user_id = job.data['user_id']
    day = job.data['day']
    time = job.data['time']
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔔 *ВРЕМЯ ТРЕНИРОВКИ!*\n\n"
                 f"📅 {day.capitalize()} в {time}\n\n"
                 f"🏊 Пора в бассейн! Не пропускай тренировку!\n"
                 f"💪 Удачи и продуктивного плавания!\n\n"
                 f"*После тренировки не забудь записать результат!*",
            parse_mode='Markdown'
        )
        logger.info(f"Отправлено напоминание пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")

# Обработка текстового ввода (для кастомных дат/времени)
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовый ввод для кастомных дат и времени"""
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    
    # Проверяем отмену
    if text in ['отмена', 'cancel', 'отменить']:
        await update.message.reply_text("❌ Установка напоминания отменена.")
        
        # Очищаем данные
        for key in ['reminder_day', 'user_id', 'waiting_for_custom_time', 
                   'waiting_for_custom_date', 'last_message_id']:
            if key in context.user_data:
                del context.user_data[key]
        
        return ConversationHandler.END
    
    # Проверяем, ждем ли мы кастомную дату
    if context.user_data.get('waiting_for_custom_date'):
        # Пытаемся распарсить дату
        try:
            if '.' in text and len(text.split('.')) == 2:
                day, month = map(int, text.split('.'))
                now = datetime.now()
                
                # Проверяем валидность даты
                if 1 <= month <= 12 and 1 <= day <= 31:
                    # Сохраняем дату в формате ДД.ММ
                    date_str = f"{day:02d}.{month:02d}"
                    context.user_data['reminder_day'] = date_str
                    context.user_data['waiting_for_custom_date'] = False
                    
                    # Сохраняем ID сообщения для редактирования
                    msg = await update.message.reply_text(
                        f"📅 Дата: {date_str}\n\n"
                        f"⏰ Теперь введи время в формате ЧЧ:ММ (например: 18:30):\n\n"
                        f"Или напиши 'отмена' для отмены"
                    )
                    context.user_data['last_message_id'] = msg.message_id
                    
                    return CHOOSING_TIME
                else:
                    await update.message.reply_text(
                        "Неверная дата. Месяц должен быть от 1 до 12, день от 1 до 31.\n"
                        "Попробуй еще раз или напиши 'отмена':"
                    )
            else:
                await update.message.reply_text(
                    "Используй формат ДД.ММ (например: 15.01)\n"
                    "Попробуй еще раз или напиши 'отмена':"
                )
        except ValueError:
            await update.message.reply_text(
                "Неверный формат. Используй ДД.ММ (например: 15.01)\n"
                "Попробуй еще раз или напиши 'отмена':"
            )
        return CHOOSING_DAY
    
    # Проверяем, ждем ли мы кастомное время
    if context.user_data.get('waiting_for_custom_time'):
        # Пытаемся распарсить время
        try:
            if ':' in text and len(text.split(':')) == 2:
                hour, minute = map(int, text.split(':'))
                
                # Проверяем валидность времени
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    time_str = f"{hour:02d}:{minute:02d}"
                    user_id = context.user_data.get('user_id', update.effective_user.id)
                    day = context.user_data['reminder_day']
                    
                    # Сохраняем напоминание
                    await save_reminder(user_id, day, time_str, context)
                    
                    # Удаляем сообщение с запросом времени
                    if 'last_message_id' in context.user_data:
                        try:
                            await context.bot.delete_message(
                                chat_id=user_id,
                                message_id=context.user_data['last_message_id']
                            )
                        except:
                            pass
                    
                    return ConversationHandler.END
                else:
                    await update.message.reply_text(
                        "Неверное время. Часы: 0-23, минуты: 0-59.\n"
                        "Попробуй еще раз или напиши 'отмена':"
                    )
            else:
                await update.message.reply_text(
                    "Используй формат ЧЧ:ММ (например: 18:30)\n"
                    "Попробуй еще раз или напиши 'отмена':"
                )
        except ValueError:
            await update.message.reply_text(
                "Неверный формат. Используй ЧЧ:ММ (например: 18:30)\n"
                "Попробуй еще раз или напиши 'отмена':"
            )
        return CHOOSING_TIME
    
    # Если это не связано с напоминаниями, обрабатываем как обычное сообщение
    return await handle_regular_message(update, context)

# Обработка регулярных сообщений
async def handle_regular_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает регулярные текстовые сообщения"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Проверяем, ждем ли мы время тренировки
    if context.user_data.get('waiting_for_time'):
        try:
            minutes = int(text)
            if 1 <= minutes <= 240:
                # Сохраняем тренировку
                if user_id not in user_trainings:
                    user_trainings[user_id] = []
                user_trainings[user_id].append(minutes)
                
                # Расчет калорий
                calories = minutes * 10
                
                await update.message.reply_text(
                    f"✅ Тренировка записана!\n\n"
                    f"⏱️ Время: {minutes} минут\n"
                    f"🔥 Калории: ~{calories}\n"
                    f"🏊 Всего тренировок: {len(user_trainings[user_id])}\n\n"
                    f"Отличная работа! 💪"
                )
                
                # Сбрасываем состояние
                context.user_data['waiting_for_time'] = False
            else:
                await update.message.reply_text("Введи время от 1 до 240 минут:")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введи число (например: 30, 45, 60):")
        return
    
    # Проверяем, ждем ли мы цель
    if context.user_data.get('waiting_for_goal'):
        goal_text = text
        
        if 'goals' not in context.user_data:
            context.user_data['goals'] = []
        
        context.user_data['goals'].append({
            'text': goal_text,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'completed': False
        })
        
        await update.message.reply_text(
            f"🎯 *Цель установлена!*\n\n"
            f"'{goal_text}'\n\n"
            f"Удачи в достижении! 💪",
            parse_mode='Markdown'
        )
        
        context.user_data['waiting_for_goal'] = False
        return
    
    # Обработка кнопок
    if text == "🏊 Записать тренировку":
        context.user_data['waiting_for_time'] = True
        
        await update.message.reply_text(
            "Отлично! Сколько минут ты плавал?\n\n"
            "Отправь число (например: 30, 45, 60):"
        )
    
    elif text == "📊 Моя статистика":
        await show_stats(update, context)
    
    elif text == "💡 Совет по плаванию":
        tips = [
            "💡 *Разминка обязательна!* 5-10 минут перед плаванием предотвратят травмы.",
            "💡 *Дыши правильно:* вдох ртом при повороте головы, выдох носом в воду.",
            "💡 *Пей воду* даже в бассейне. Плавание вызывает обезвоживание!",
            "💡 *Начни с брасса* - самый простой стиль для новичков.",
            "💡 *Используй очки* - защитят глаза и улучшат видимость.",
            "💡 *После тренировки* делай заминку и растяжку.",
            "💡 *Регулярность важнее* интенсивности. Лучше 3×30 мин, чем 1×2 часа.",
            "💡 *Не ешь* за 1-2 часа до плавания.",
            "💡 *Слушай тело:* если болит - отдохни или уменьши нагрузку.",
            "💡 *Ставь цели:* например, проплыть 1000м без остановки."
        ]
        
        tip = random.choice(tips)
        await update.message.reply_text(tip, parse_mode='Markdown')
    
    elif text == "🎯 Поставить цель":
        context.user_data['waiting_for_goal'] = True
        
        await update.message.reply_text(
            "🎯 *Постановка цели*\n\n"
            "Примеры целей:\n"
            "• Проплыть 1000 метров без остановки\n"
            "• Заниматься 3 раза в неделю\n"
            "• Плавать суммарно 5 часов в месяц\n\n"
            "Напиши свою цель:",
            parse_mode='Markdown'
        )
    
    elif text == "🔔 Мои напоминания":
        await show_reminders_menu(update, context)
    
    else:
        # Если это произвольный текст
        responses = [
            f"Я понял: '{text}'\n\nИспользуй кнопки для лучшего взаимодействия! 🏊",
            f"Ты написал: '{text}'\n\nПопробуй воспользоваться кнопками ниже!",
            f"Сообщение получено: '{text}'\n\nВыбери действие из меню! 💪"
        ]
        await update.message.reply_text(random.choice(responses))

# Удалить все напоминания
async def delete_all_reminders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет все напоминания пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id in user_reminders:
        # Помечаем все напоминания как неактивные
        for reminder in user_reminders[user_id]:
            reminder['active'] = False
        user_reminders[user_id] = []
    
    await query.edit_message_text(
        "✅ Все напоминания удалены!\n\n"
        "Ты можешь добавить новые напоминания."
    )

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущее действие"""
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *Помощь по AI помощнику FitSwim*

*Основные команды:*
/start - Запустить бота (показать кнопки)
/help - Эта справка
/tip - Случайный совет
/stats - Быстрая статистика
/reminders - Мои напоминания
/reset - Сбросить все данные
/test_reminder - Тест напоминания (на 1 минуту)

*Основные кнопки:*
🏊 Записать тренировку - записать время плавания
📊 Моя статистика - посмотреть прогресс
💡 Совет по плаванию - получить полезный совет
🎯 Поставить цель - установить новую цель
🔔 Мои напоминания - управление напоминаниями

*Как работает система напоминаний:*
1. Нажми "🔔 Мои напоминания"
2. Нажми инлайн-кнопку "➕ Установить напоминание"
3. Выбери день или введи свою дату
4. Выбери время или введи свое время
5. Получи уведомление в нужное время!

*Для быстрой проверки:* используй команду /test_reminder

Удачи в плавании! 🏊‍♂️
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Команда /stats
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_stats(update, context)

# Команда /tip
async def tip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tips = [
        "💡 Плавание развивает все группы мышц равномерно!",
        "💡 В воде нагрузка на суставы меньше на 90%!",
        "💡 Плавание улучшает осанку и гибкость!",
        "💡 Регулярное плавание снижает стресс!",
        "💡 Это отличная кардио-тренировка для сердца!"
    ]
    await update.message.reply_text(random.choice(tips))

# Команда /reminders
async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_reminders_menu(update, context)

# Команда /test_reminder - тест напоминания
async def test_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для проверки напоминаний"""
    user_id = update.effective_user.id
    
    # Устанавливаем тестовое напоминание на 1 минуту вперед
    test_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    
    if user_id not in user_reminders:
        user_reminders[user_id] = []
    
    test_reminder = {
        'day': 'сегодня',
        'time': test_time,
        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'active': True
    }
    
    user_reminders[user_id].append(test_reminder)
    
    # Планируем напоминание
    success = await schedule_reminder(user_id, 'сегодня', test_time, context)
    
    if success:
        await update.message.reply_text(
            f"✅ Тестовое напоминание установлено!\n\n"
            f"📅 Сегодня в {test_time}\n\n"
            f"Уведомление придет через 1 минуту для проверки."
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось установить тестовое напоминание.\n"
            "Попробуй еще раз или проверь настройки бота."
        )

# Команда /test - для проверки
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ FitSwim AI помощник работает!\n\n"
        "Для теста напоминаний используй команду:\n"
        "/test_reminder\n\n"
        "Бот установит напоминание на 1 минуту вперед."
    )

# Главная функция
def main():
    """Запуск бота"""
    
    print("=" * 70)
    print("🤖 ЗАПУСК AI ПОМОЩНИКА FITSWIM")
    print("=" * 70)
    
    # Проверка токена
    if not BOT_TOKEN or len(BOT_TOKEN) < 20:
        print("❌ ОШИБКА: Неверный токен!")
        return
    
    print(f"✅ Токен: {BOT_TOKEN[:10]}...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        print("✅ Приложение создано")
        
        # Создаем ConversationHandler для напоминаний
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(start_reminder, pattern="^start_reminder$"),
            ],
            states={
                CHOOSING_DAY: [
                    CallbackQueryHandler(choose_day, pattern="^day_|^cancel$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
                ],
                CHOOSING_TIME: [
                    CallbackQueryHandler(choose_time, pattern="^time_|^cancel$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        # Добавляем обработчики КОМАНД
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("tip", tip_command))
        application.add_handler(CommandHandler("reminders", reminders_command))
        application.add_handler(CommandHandler("test_reminder", test_reminder_command))
        application.add_handler(CommandHandler("test", test_command))
        print("✅ Обработчики команд добавлены")
        
        # Добавляем ConversationHandler
        application.add_handler(conv_handler)
        print("✅ ConversationHandler для напоминаний добавлен")
        
        # Добавляем обработчики для кнопок меню напоминаний
        application.add_handler(CallbackQueryHandler(show_my_reminders_callback, pattern="^show_my_reminders$"))
        application.add_handler(CallbackQueryHandler(delete_all_reminders_callback, pattern="^delete_all_reminders$"))
        application.add_handler(CallbackQueryHandler(back_to_reminders_menu, pattern="^back_to_reminders_menu$"))
        print("✅ Обработчики кнопок меню напоминаний добавлены")
        
        # Добавляем обработчик ВСЕХ текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_regular_message))
        print("✅ Обработчик сообщений добавлен")
        
        print("\n" + "=" * 70)
        print("🚀 FITSWIM УСПЕШНО ЗАПУЩЕН!")
        print("=" * 70)
        print("\n📱 В Telegram:")
        print("1. Напишите /start")
        print("2. Нажмите '📊 Моя статистика' - покажет статистику")
        print("3. Нажмите '🔔 Мои напоминания' - управление напоминаниями")
        print("4. В меню напоминаний нажмите '➕ Установить напоминание'")
        print("5. Выберите день и время")
        print("6. Или для быстрого теста: /test_reminder")
        print("\n🛑 Ctrl+C для остановки")
        print("=" * 70)
        
        # Запускаем бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ЗАПУСКА: {e}")
        print("\nПопробуйте:")
        print("1. Перезапустить бота")
        print("2. Проверить интернет соединение")
        print("3. Написать /start в боте")

if __name__ == '__main__':
    main()