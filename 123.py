import sqlite3
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# ===== НАСТРОЙКИ =====
TOKEN = "8479652082:AAF87h20MH0fF6ZCHXupk6EPSml5CvY8AIE"
ADMIN_ID = 5059000308
LOG_GROUP_ID = -1003699875240
PHOTO_PATH = r"фото бота/фото.jpg"

CHAT_LINK = "https://t.me/+LsYbmlmhBJoxYzgy"
BUILDER_LINK = "https://t.me/chm_builder_bot"
KEY_LINK = "https://t.me/chm_work_bot"

EXPERIENCE, SOURCE = range(2)

# ===== БАЗА =====
db = sqlite3.connect("users.db", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    experience TEXT,
    source TEXT,
    approved INTEGER DEFAULT 0
)
""")
db.commit()

# === МИГРАЦИЯ role ===
try:
    sql.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Новичок'")
    db.commit()
except sqlite3.OperationalError:
    pass


def is_approved(user_id):
    sql.execute("SELECT approved FROM users WHERE user_id=?", (user_id,))
    row = sql.fetchone()
    return row and row[0] == 1


# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_approved(update.effective_user.id):
        await send_main_menu(update, context)
        return ConversationHandler.END

    await update.message.reply_text("❓ Есть ли у вас опыт в ворке?")
    return EXPERIENCE


async def save_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text
    await update.message.reply_text("❓ Откуда вы о нас узнали?")
    return SOURCE


async def save_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    sql.execute(
        "INSERT OR REPLACE INTO users (user_id, experience, source, approved, role) VALUES (?, ?, ?, 0, 'Новичок')",
        (user.id, context.user_data["experience"], update.message.text)
    )
    db.commit()

    text = (
        "🆕 *Новая заявка*\n\n"
        f"👤 {user.first_name}\n"
        f"🆔 `{user.id}`"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user.id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")
    ]])

    await context.bot.send_message(LOG_GROUP_ID, text, reply_markup=keyboard, parse_mode="Markdown")
    await update.message.reply_text("⏳ Заявка отправлена.")
    return ConversationHandler.END


# ===== APPROVE / REJECT =====
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, user_id = q.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        sql.execute("UPDATE users SET approved=1 WHERE user_id=?", (user_id,))
        db.commit()
        await context.bot.send_message(user_id, "✅ Заявка одобрена! Напиши /start")
        await q.edit_message_text(q.message.text + "\n\n✅ Одобрено")

    else:
        await context.bot.send_message(user_id, "❌ Заявка отклонена")
        await q.edit_message_text(q.message.text + "\n\n❌ Отклонено")


# ===== ГЛАВНОЕ МЕНЮ =====
async def send_main_menu(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠️ Создать АПК", callback_data="key_builder")],
        [
            InlineKeyboardButton("📜 Мануалы", callback_data="manuals"),
            InlineKeyboardButton("📚 Полезное", callback_data="useful")
        ],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("💬 Чатик", url=CHAT_LINK)]
    ])

    await context.bot.send_photo(
        update.effective_chat.id,
        open(PHOTO_PATH, "rb"),
        caption="🔥 *Sparta Team* — добро пожаловать!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ===== ПОДМЕНЮ =====
async def key_builder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.edit_message_reply_markup(
        InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Создать билд", url=BUILDER_LINK)],
            [InlineKeyboardButton("🔑 Получить ключ", url=KEY_LINK)],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
        ])
    )


async def manuals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.edit_message_reply_markup(
        InlineKeyboardMarkup([
            [InlineKeyboardButton("📘 Баззовый пролив", url="https://t.me/+a0mBusYSHEwwNmIy")],
            [InlineKeyboardButton("📕 Выди проливов", url="https://t.me/+7-58tFin0LoyOWI6")],
            [InlineKeyboardButton("📗 Мануал По СЗ Rat", url="https://telegra.ph/MANUAL-PO-C3-RAT-11-16")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
        ])
    )


async def useful_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.edit_message_reply_markup(
        InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Логи", url="https://t.me/+MGIzRMwwlsM1NmYy")],
            [InlineKeyboardButton("🔁 Ретранс", url="https://t.me/+0IlXpnhIT_80NjFi")],
            [InlineKeyboardButton("🤖 Бот Отстуки", url="https://t.me/spteam_sms_bot")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
        ])
    )


async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await send_main_menu(update, context)


# ===== ПРОФИЛЬ =====
async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    sql.execute("SELECT role FROM users WHERE user_id=?", (q.from_user.id,))
    role = sql.fetchone()

    await q.message.reply_text(
        f"👤 *Профиль*\n ``\n🎭 Роль: *{role[0] if role else 'Новичок'}*",
        parse_mode="Markdown"
    )


# ===== /role =====
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])
    role = " ".join(context.args[1:])

    sql.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    db.commit()
    await update.message.reply_text("✅ Роль обновлена")


# ===== RUN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_experience)],
            SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_source)]
        },
        fallbacks=[]
    ))

    app.add_handler(CallbackQueryHandler(callbacks, pattern="^(approve|reject)_"))
    app.add_handler(CallbackQueryHandler(key_builder_menu, pattern="^key_builder$"))
    app.add_handler(CallbackQueryHandler(manuals_menu, pattern="^manuals$"))
    app.add_handler(CallbackQueryHandler(useful_menu, pattern="^useful$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(profile_callback, pattern="^profile$"))
    app.add_handler(CommandHandler("role", set_role))

    print("🔥 Sparta Team bot запущен")
    app.run_polling()


if __name__ == "__main__":
    main()

