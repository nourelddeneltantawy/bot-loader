cat << 'EOF' > bot.py
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
        "أرسل لي رابط المقطع (يوتيوب، فيسبوك، تيك توك، إلخ)، وسأتيح لك خيارات التحميل.\n\n"
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
            InlineKeyboardButton("🔊 تحميل صوت (MP3)", callback_data='audio')
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

    await query.edit_message_text("جاري استخراج وتحميل المقطع... برجاء الانتظار ⏳")

    file_path = None
    output_template = f"downloads/{query.from_user.id}_%(id)s.%(ext)s"

    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_template,
        'nocheckcertificate': True,
    }

    if choice == 'video':
        ydl_opts = {
            **common_opts,
            'format': 'best[ext=mp4]/best',
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
                base, _ = os.path.splitext(file_path)
                file_path = base + ".mp3"

        await query.message.reply_text("جاري رفع الملف إلى المحادثة... 📤")

        caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

        with open(file_path, 'rb') as f:
            if choice == 'video':
                await query.message.reply_video(video=f, caption=caption_text)
            else:
                await query.message.reply_audio(audio=f, caption=caption_text)

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await query.message.reply_text(f"حدث خطأ أثناء التنزيل: {str(e)[:100]}")
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
EOF
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

    await query.edit_message_text("جاري استخراج وتحميل المقطع... برجاء الانتظار ⏳")

    file_path = None
    output_template = f"downloads/{query.from_user.id}_%(id)s.%(ext)s"

    # خيارات متقدمة لتجاوز حظر يوتيوب وفيسبوك وتظليل حماية السيرفرات
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_template,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        }
    }

    if choice == 'video':
        ydl_opts = {
            **common_opts,
            'format': 'best[ext=mp4]/bestvideo+bestaudio/best',
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
            
            # ضبط الامتداد في حالة تحويل الصوت لـ MP3
            if choice == 'audio':
                base, _ = os.path.splitext(file_path)
                file_path = base + ".mp3"

        # التحقق من أن حجم الملف لا يتجاوز 50 ميجا (حد تليجرام البوتات)
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 49:
            await query.message.reply_text("عذراً، حجم هذا الملف أكبر من 50 ميجابايت (الحد الأقصى المسموح للبوتات المجانية في تليجرام).")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        await query.message.reply_text("جاري رفع الملف إلى المحادثة... 📤")

        caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

        with open(file_path, 'rb') as f:
            if choice == 'video':
                await query.message.reply_video(video=f, caption=caption_text)
            else:
                await query.message.reply_audio(audio=f, caption=caption_text)

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await query.message.reply_text("حدث خطأ أثناء التنزيل. قد يكون المقطع خاصاً أو محميًا ضد التنزيل الآلي.")
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
        video_url = None
        if "data" in data and "downloadUrl" in data["data"]:
            video_url = data["data"]["downloadUrl"]
        elif "download" in data:
            video_url = data["download"]

        if video_url:
            file_path = f"downloads/{update.message.from_user.id}.mp4"
            
            # تنزيل ملف الفيديو
            video_bytes = requests.get(video_url, stream=True, timeout=60)
            with open(file_path, 'wb') as f:
                for chunk in video_bytes.iter_content(chunk_size=16384):
                    f.write(chunk)

            await msg.edit_text("جاري رفع الفيديو إلى المحادثة... 📤")
            caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

            with open(file_path, 'rb') as f:
                await update.message.reply_video(video=f, caption=caption_text)

            if os.path.exists(file_path):
                os.remove(file_path)
            
            await msg.delete()

        else:
            await msg.edit_text("عذراً، تعذر جلب رابط الفيديو من هذا المصدر.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text("حدث خطأ أثناء معالجة المقطع. حاول مرة أخرى أو جرب رابطاً آخر.")

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
