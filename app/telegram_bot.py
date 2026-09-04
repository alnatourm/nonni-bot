import asyncio
import logging
import time
from collections import defaultdict, deque

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
    clear_memories,
    delete_user_data,
    get_memories,
    get_or_create_user,
    prune_history,
    prune_memories,
    save_memory,
    save_message,
)
from .documents import SUPPORTED_DOCUMENTS, extract_document
from .ai import ai_provider
from .router import generate_response


logger = logging.getLogger("nonni.telegram")
request_times: dict[int, deque[float]] = defaultdict(deque)
user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)


async def ensure_authorized(update: Update) -> bool:
    user = update.effective_user
    if user and (
        not settings.allowed_user_ids or user.id in settings.allowed_user_ids
    ):
        return True
    if update.effective_message:
        await update.effective_message.reply_text(
            "هذا البوت خاص وغير متاح لهذا الحساب."
        )
    return False


def rate_limit_remaining(user_id: int) -> int:
    now = time.monotonic()
    window = request_times[user_id]
    while window and now - window[0] >= 60:
        window.popleft()
    if len(window) >= settings.requests_per_minute:
        return max(1, int(60 - (now - window[0])))
    window.append(now)
    return 0


def split_message(text: str, limit: int = 4096) -> list[str]:
    """Split at line or space boundaries when possible."""
    chunks = []
    remaining = text.strip()
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, limit + 1)
        if cut < limit // 2:
            cut = remaining.rfind(" ", 0, limit + 1)
        if cut < limit // 2:
            cut = limit
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    return chunks or [""]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    user = update.effective_user
    await get_or_create_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )
    text = (
        f"مرحباً {user.first_name} 👋\n\n"
        "أنا Nonni 🤖، مساعد محادثة نصي بالعربية والإنجليزية.\n\n"
        "الأوامر:\n"
        "/clear - مسح المحادثة\n"
        "/remember [ملاحظة] - حفظ ملاحظة\n"
        "/memory - عرض الذاكرة\n"
        "/forget - مسح الذاكرة\n"
        "/delete_me - حذف جميع بياناتك المحلية\n\n"
        "/model - عرض نموذج الذكاء الاصطناعي المستخدم\n\n"
        "/web [سؤال] - بحث مباشر في الويب\n"
        "/weather [مدينة] - الطقس المباشر\n\n"
        "يمكنك أيضًا إرسال صورة أو ملف PDF/DOCX/TXT/CSV/MD/JSON."
    )
    await update.message.reply_text(text)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    await clear_history(update.effective_user.id)
    await update.message.reply_text("🧹 تم مسح سجل المحادثة.")


async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    user = update.effective_user
    note = " ".join(context.args).strip() if context.args else ""
    if not note:
        await update.message.reply_text("❌ اكتب ما تريد حفظه بعد /remember")
        return
    if len(note) > 1000:
        await update.message.reply_text("❌ الملاحظة طويلة جدًا؛ الحد 1000 حرف.")
        return
    await save_memory(user.id, "note", note, importance=1)
    await prune_memories(user.id, settings.max_memory_items)
    await update.message.reply_text("✅ تم حفظ الملاحظة.")


async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    memories = await get_memories(update.effective_user.id, settings.max_memory_items)
    if not memories:
        await update.message.reply_text("📭 لا توجد ذاكرة محفوظة.")
        return
    lines = ["🧠 ذاكرتك المحفوظة:\n"]
    lines.extend(f"• [{item.memory_type}] {item.content}" for item in memories)
    for chunk in split_message("\n".join(lines)):
        await update.message.reply_text(chunk)


async def forget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    await clear_memories(update.effective_user.id)
    await update.message.reply_text("🧹 تم مسح الذاكرة المحفوظة.")


async def delete_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    user_id = update.effective_user.id
    await delete_user_data(user_id)
    request_times.pop(user_id, None)
    await update.message.reply_text(
        "✅ تم حذف محادثاتك وذاكرتك وبيانات حسابك المحلية."
    )


async def model_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    await update.message.reply_text(
        "🤖 Model: " + settings.groq_model + "\n⚡ Provider: Groq"
    )


async def web_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("اكتب سؤالك بعد /web")
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    response, _ = await generate_response(update.effective_user.id, query, force_web=True)
    for chunk in split_message(response):
        await update.message.reply_text(chunk)


async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update):
        return
    location = " ".join(context.args).strip()
    if not location:
        await update.message.reply_text("اكتب المدينة بعد /weather، مثال: /weather Amman")
        return
    query = f"Give the current weather and forecast for {location}. Include dates and units."
    await update.message.chat.send_action(ChatAction.TYPING)
    response, _ = await generate_response(update.effective_user.id, query, force_web=True)
    for chunk in split_message(response):
        await update.message.reply_text(chunk)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update) or not settings.enable_documents:
        return
    document = update.message.document
    filename = document.file_name or "document"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in SUPPORTED_DOCUMENTS:
        await update.message.reply_text("نوع الملف غير مدعوم. أرسل PDF أو DOCX أو TXT أو CSV أو MD أو JSON.")
        return
    if document.file_size and document.file_size > settings.max_file_size_mb * 1024 * 1024:
        await update.message.reply_text(f"الملف أكبر من الحد المسموح: {settings.max_file_size_mb} MB")
        return
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        telegram_file = await context.bot.get_file(document.file_id)
        data = bytes(await telegram_file.download_as_bytearray())
        extracted = extract_document(data, filename, settings.max_document_chars)
        question = update.message.caption or "Summarize this document and list its key points."
        response, _ = await generate_response(
            update.effective_user.id, question, additional_context=extracted
        )
        for chunk in split_message(response):
            await update.message.reply_text(chunk)
    except Exception as exc:
        logger.exception("Document analysis failed: %s", exc)
        await update.message.reply_text("تعذر قراءة الملف. تأكد أنه غير تالف أو محمي بكلمة مرور.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_authorized(update) or not settings.enable_vision:
        return
    photo = update.message.photo[-1]
    if photo.file_size and photo.file_size > settings.max_file_size_mb * 1024 * 1024:
        await update.message.reply_text(f"الصورة أكبر من الحد المسموح: {settings.max_file_size_mb} MB")
        return
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        telegram_file = await context.bot.get_file(photo.file_id)
        data = bytes(await telegram_file.download_as_bytearray())
        prompt = update.message.caption or "Describe and analyze this image clearly."
        response = await ai_provider.vision(data, "image/jpeg", prompt)
        for chunk in split_message(response):
            await update.message.reply_text(chunk)
    except Exception as exc:
        logger.exception("Image analysis failed: %s", exc)
        await update.message.reply_text("تعذر تحليل الصورة. حاول بصورة JPG أو PNG أصغر.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if not await ensure_authorized(update):
        return
    user = update.effective_user
    user_text = update.message.text.strip()
    if not user_text:
        return
    if len(user_text) > settings.max_message_length:
        await update.message.reply_text("❌ الرسالة طويلة جدًا.")
        return
    wait_seconds = rate_limit_remaining(user.id)
    if wait_seconds:
        await update.message.reply_text(
            f"طلبات كثيرة جدًا. حاول مرة أخرى بعد {wait_seconds} ثانية."
        )
        return

    await get_or_create_user(user.id, user.first_name, user.username)
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        async with user_locks[user.id]:
            response, _intent = await generate_response(user.id, user_text)
            if not response.strip():
                raise RuntimeError("AI returned an empty response")

            # Saving happens after generation so the current message is not
            # duplicated in both history and the new API request.
            await save_message(user.id, "user", user_text)
            await save_message(user.id, "assistant", response)
            await prune_history(user.id, settings.max_history)

        for chunk in split_message(response):
            await update.message.reply_text(chunk)
    except Exception as exc:
        logger.exception("AI request failed: %s", exc)
        await update.message.reply_text(
            "حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى بعد قليل. 🔄"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled Telegram error", exc_info=context.error)


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
    application.add_handler(CommandHandler("forget", forget))
    application.add_handler(CommandHandler("delete_me", delete_me))
    application.add_handler(CommandHandler("model", model_cmd))
    application.add_handler(CommandHandler("web", web_cmd))
    application.add_handler(CommandHandler("weather", weather_cmd))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    application.add_error_handler(error_handler)
    return application
