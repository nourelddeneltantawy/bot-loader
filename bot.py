import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = '8736078197:AAGfMdjV12D9mbRt8oj4nXkC1og3mJxJajQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "السلام عليكم ورحمة الله وبركاته 🍃\n\n"
        "أهلاً بك في بوت التحميل الشامل من أبو البراء.\n"
        "أرسل لي رابط المقطع (يوتيوب، فيسبوك، تيك توك، إلخ)، وسأتيح لك خيارات تحويله إلى فيديو أو صوت.\n\n"
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

    file_path = None
    output_template = f"downloads/{query.from_user.id}_%(id)s.%(ext)s"

    # خيارات محسنة لتجاوز قيود وحظر يوتيوب على السيرفرات
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_template,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    if choice == 'video':
        ydl_opts = {
            **common_opts,
            # يجلب مقطع جهيز ومدمج بصوت وصورة مباشرة لتفادي الحاجة لـ ffmpeg
            'format': 'best[ext=mp4]/best',
        }
    else:
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await query.message.reply_text("جاري رفع الملف إليك... 📤")

        caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

        with open(file_path, 'rb') as f:
            if choice == 'video':
                await query.message.reply_video(video=f, caption=caption_text)
            else:
                await query.message.reply_audio(audio=f, caption=caption_text)

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await query.message.reply_text(f"حدث خطأ أثناء المعالجة: {str(e)[:100]}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    app.run_polling()
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

    file_path = None
    output_template = f"downloads/{query.from_user.id}_%(id)s.%(ext)s"

    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_template,
        'maxfilesize': 50 * 1024 * 1024,
    }

    if choice == 'video':
        ydl_opts = {
            **common_opts,
            'format': 'bestvideo[filesize<45M]+bestaudio/best[filesize<45M]/best',

        }
    else:
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if choice == 'audio':
                file_path = os.path.splitext(file_path)[0] + '.mp3'

        await query.message.reply_text("جاري رفع الملف إليك... 📤")

        caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

        if choice == 'video':
            with open(file_path, 'rb') as f:
                await query.message.reply_video(video=f, caption=caption_text)
        else:
            with open(file_path, 'rb') as f:
                await query.message.reply_audio(audio=f, caption=caption_text)

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await query.message.reply_text("حدث خطأ أثناء التحميل. قد يكون الحجم كبيراً جداً (أكثر من 50 ميجا) أو أن المقطع محمي.")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    app.run_polling()
              
