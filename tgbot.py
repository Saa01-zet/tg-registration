import json
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

USERS_FILE = "users.json"


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для регистрации.\n\nКоманды:\n/register - регистрация\n/login - вход\n/me - кто я\n/logout - выйти")


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user_id = str(update.effective_user.id)

    for login, data in users.items():
        if data.get("user_id") == user_id:
            await update.message.reply_text(f"Ты уже зарегистрирован как {login}! Используй /login")
            return

    if "step" not in context.user_data:
        context.user_data["step"] = "reg_login"
        await update.message.reply_text("Введите логин:")
        return

    if context.user_data["step"] == "reg_login":
        login = update.message.text.strip()
        if login in users:
            await update.message.reply_text("Такой логин уже есть! Введите другой:")
            return
        if len(login) < 3:
            await update.message.reply_text("Логин должен быть минимум 3 символа:")
            return
        context.user_data["new_login"] = login
        context.user_data["step"] = "reg_pass"
        await update.message.reply_text("Введите пароль:")
        return

    if context.user_data["step"] == "reg_pass":
        password = update.message.text.strip()
        if len(password) < 4:
            await update.message.reply_text("Пароль должен быть минимум 4 символа:")
            return
        login = context.user_data["new_login"]

        users[login] = {
            "password": password,
            "user_id": str(update.effective_user.id)
        }
        save_users(users)

        context.user_data["current_user"] = login
        del context.user_data["step"]
        del context.user_data["new_login"]

        await update.message.reply_text(f"✅ Регистрация прошла успешно! Ты вошел как {login}")


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "current_user" in context.user_data:
        await update.message.reply_text(f"Ты уже вошел как {context.user_data['current_user']}")
        return

    if "step" not in context.user_data:
        context.user_data["step"] = "login_login"
        await update.message.reply_text("Введите логин:")
        return

    if context.user_data["step"] == "login_login":
        login = update.message.text.strip()
        users = load_users()
        if login not in users:
            await update.message.reply_text("Пользователь не найден! Введите логин еще раз:")
            return
        context.user_data["auth_login"] = login
        context.user_data["step"] = "login_pass"
        await update.message.reply_text("Введите пароль:")
        return

    if context.user_data["step"] == "login_pass":
        password = update.message.text.strip()
        login = context.user_data["auth_login"]
        users = load_users()

        if users[login]["password"] != password:
            await update.message.reply_text("❌ Неверный пароль! Попробуй /login заново")
            del context.user_data["step"]
            del context.user_data["auth_login"]
            return

        context.user_data["current_user"] = login
        del context.user_data["step"]
        del context.user_data["auth_login"]

        await update.message.reply_text(f"✅ Вход выполнен! Привет, {login}")


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "current_user" in context.user_data:
        await update.message.reply_text(f"Твой логин: {context.user_data['current_user']}")
    else:
        await update.message.reply_text("Ты не вошел в аккаунт! Используй /login")


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "current_user" in context.user_data:
        user = context.user_data["current_user"]
        del context.user_data["current_user"]
        await update.message.reply_text(f"Ты вышел из аккаунта {user}")
    else:
        await update.message.reply_text("Ты и так не в аккаунте")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "step" in context.user_data:
        if context.user_data["step"] in ["reg_login", "reg_pass"]:
            await register(update, context)
        elif context.user_data["step"] in ["login_login", "login_pass"]:
            await login(update, context)
    else:
        await update.message.reply_text("Используй команды: /register или /login")


def main():
    TOKEN = "8256180076:AAEMCq2NXwzRB7umjZlZZr0jcZg-JlbHHqc"

    print("🚀 Запуск бота...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен! Напиши /start в Telegram")

    try:
        app.run_polling()
    except RuntimeError as e:
        if "no current event loop" in str(e):
            # Создаем event loop для Python 3.14+
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            app.run_polling()
        else:
            raise


if __name__ == "__main__":
    main()