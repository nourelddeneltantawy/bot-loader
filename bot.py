import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = '8736078197:AAGfMdjV12D9mbRt8oj4nXkC1og3mJxJajQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "السلام عليكم ورحمة الله وبركاته 🍃\n\n"
        "أهلاً بك في بوت التحميل المباشر من أبو البراء.\n"
        "أرسل لي رابط المقطع فوراً، وسأقوم بتحميله وإرساله لك هنا مباشرةً.\n\n"
        "﴿وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا﴾\n"
        "⚠️ يرجى عدم استخدام البوت في تحميل ما يغضب الله تعالى."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    msg = await update.message.reply_text("جاري استخراج المقطع والتحميل... برجاء الانتظار ⏳")

    try:
        # استخدام خادم تنزيل مخصص يلتف على حظر السيرفرات
        clean_url = requests.utils.quote(url, safe='')
        download_api = f"https://api.vkrdown.com/v1/main?url={clean_url}"
        
        resp = requests.get(download_api, timeout=20)
        data = resp.json()

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
