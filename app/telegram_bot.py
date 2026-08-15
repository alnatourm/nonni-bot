import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import settings
from .database import (
    clear_history,
    get_or_create_user,
    save_message,
    save_memory,
)
from .memory import detect_language
from .router import generate_response


logger = logging.getLogger("nonni.telegram")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    await get_or_create_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )

    text = (
        f"مرحباً {user.first_name} 👋\n\n"
        "أنا Nonni 🤖\n\n"
        "أستطيع مساعدتك في:\n"
        "💻 البرمجة\n"
        "💼 الأعمال\n"
        "📊 تحليل المشاريع\n"
        "🤖 الذكاء الاصطناعي\n"
        "🍳 الطبخ\n"
        "☪️ المعرفة الإسلامية\n"
        "🌐 العربية والإنجليزية\n\n"
        "الأوامر:\n"
        "/start - إعادة تشغيل\n"
        "/clear - مسح المحادثة\n"
        "/remember [ملاحظة] - حفظ ملاحظة\n"
        "/memory - عرض الذاكرة\n\n"
        "أرسل لي أي سؤال للبدء! 🚀"
    )

    await update.message.reply_text(text)


async def clear(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    await clear_history(user.id)
    await update.message.reply_text("🧹 تم مسح سجل المحادثة.")


async def remember(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    note = " ".join(context.args) if context.args else ""

    if not note:
        await update.message.reply_text("❌ اكتب ما تريد حفظه بعد /remember")
        return

    await save_memory(
        telegram_user_id=user.id,
        memory_type="note",
        content=note,
        importance=1,
    )

    await update.message.reply_text(f"✅ تم الحفظ: {note}")


async def memory_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    from .database import get_memories

    user = update.effective_user
    memories = await get_memories(user.id, 20)

    if not memories:
        await update.message.reply_text("📭 لا توجد ذاكرة محفوظة.")
        return

    lines = ["🧠 ذاكرتك المحفوظة:\n"]
    for m in memories:
        lines.append(f"• [{m.memory_type}] {m.content}")

    await update.message.reply_text("\n".join(lines))


async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    user_text = update.message.text.strip()

    if not user_text:
        return

    if len(user_text) > settings.max_message_length:
        await update.message.reply_text("❌ الرسالة طويلة جدًا.")
        return

    await get_or_create_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )

    await save_message(
        telegram_user_id=user.id,
        role="user",
        content=user_text,
    )

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response, intent = await generate_response(
            telegram_user_id=user.id,
            user_text=user_text,
        )

        await save_message(
            telegram_user_id=user.id,
            role="assistant",
            content=response,
        )

        # Telegram message limit is 4096
        max_length = 4096

        for start in range(0, len(response), max_length):
            chunk = response[start:start + max_length]
            await update.message.reply_text(chunk)

    except Exception as exc:
        logger.exception("AI request failed: %s", exc)
        await update.message.reply_text(
            "حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى بعد قليل. 🔄"
        )


def create_application():
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("remember", remember))
    application.add_handler(CommandHandler("memory", memory_cmd))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    return application
