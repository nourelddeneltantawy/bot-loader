import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = '8736078197:AAGfMdjV12D9mbRt8oj4nXkC1og3mJxJajQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "السلام عليكم ورحمة الله وبركاته 🍃\n\n"
        "أهلاً بك في بوت التحميل الشامل من أبو البراء.\n"
        "أرسل لي رابط المقطع (يوتيوب، تيك توك، إلخ)، وسأتيح لك خيارات التحميل.\n\n"
        "﴿وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا﴾\n"
        "⚠️ يرجى عدم استخدام البوت في تحميل ما يغضب الله تعالى."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    context.user_data['download_url'] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 تحميل فيديو", callback_data='video'),
            InlineKeyboardButton("🔊 تحميل صوت فقط", callback_data='audio')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "اختر الصيغة التي تريد تحميل المقطع بها:",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    url = context.user_data.get('download_url')

    if not url:
        await query.edit_message_text("حدث خطأ، يرجى إعادة إرسال الرابط مرة أخرى.")
        return

    await query.edit_message_text("جاري معالجة الرابط وتحميل المقطع... برجاء الانتظار ⏳")

    try:
        # استدعاء API وسيط يتجاوز حظر السيرفرات لليوتيوب
        api_url = f"https://api.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "downloadMode": "audio" if choice == 'audio' else "auto"
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        data = response.json()

        if "url" in data:
            download_link = data["url"]
            file_req = requests.get(download_link, stream=True, timeout=30)
            
            ext = "mp3" if choice == 'audio' else "mp4"
            file_path = f"downloads/{query.from_user.id}.{ext}"

            with open(file_path, 'wb') as f:
                for chunk in file_req.iter_content(chunk_size=8192):
                    f.write(chunk)

            await query.message.reply_text("جاري رفع الملف إليك... 📤")
            caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

            with open(file_path, 'rb') as f:
                if choice == 'video':
                    await query.message.reply_video(video=f, caption=caption_text)
                else:
                    await query.message.reply_audio(audio=f, caption=caption_text)

            if os.path.exists(file_path):
                os.remove(file_path)

        else:
            await query.message.reply_text("عذراً، لم نتمكن من استخراج رابط مباشر لهذا المقطع حالياً.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await query.message.reply_text("تعذر التحميل، قد يكون المقطع خاصاً أو يتجاوز الحجم المسموح للرفع.")

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    app.run_polling()
