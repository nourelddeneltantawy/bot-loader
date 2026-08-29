import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = '8736078197:AAGfMdjV12D9mbRt8oj4nXkC1og3mJxJajQ'

def extract_video_id(url):
    """استخراج معرف الفيديو من رابط يوتيوب أو شورتس"""
    if 'shorts/' in url:
        return url.split('shorts/')[1].split('?')[0].split('/')[0]
    elif 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "السلام عليكم ورحمة الله وبركاته 🍃\n\n"
        "أهلاً بك في بوت التحميل المباشر من أبو البراء.\n"
        "أرسل لي رابط المقطع، وسأقوم بتحميله وإرساله لك هنا مباشرةً.\n\n"
        "﴿وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا﴾\n"
        "⚠️ يرجى عدم استخدام البوت في تحميل ما يغضب الله تعالى."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    msg = await update.message.reply_text("جاري معالجة الرابط وتحميل الفيديو... برجاء الانتظار ⏳")

    try:
        video_id = extract_video_id(url)
        
        if not video_id:
            await msg.edit_text("عذراً، لم نتمكن من التعرف على رابط يوتيوب/شورتس بشكل صحيح.")
            return

        # استخدام Piped API المخصص لتجاوز حظر يوتيوب على الخوادم
        piped_api = f"https://pipedapi.kavin.rocks/streams/{video_id}"
        resp = requests.get(piped_api, timeout=15)
        
        if resp.status_code != 200:
            # تجربة سيرفر بديل لـ Piped في حال ضغط السيرفر الأول
            piped_api = f"https://api.piped.video/streams/{video_id}"
            resp = requests.get(piped_api, timeout=15)

        data = resp.json()
        video_streams = data.get('videoStreams', [])

        # البحث عن أفضل فيديو يحتوي على صوت وصورة مدمجين وتجاوز الـ 50 ميجا
        direct_url = None
        for stream in video_streams:
            if stream.get('videoOnly') is False:
                direct_url = stream.get('url')
                break

        if not direct_url and video_streams:
            direct_url = video_streams[0].get('url')

        if direct_url:
            file_path = f"downloads/{update.message.from_user.id}.mp4"
            
            # تنزيل الملف
            with requests.get(direct_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=16384):
                        f.write(chunk)

            # التأكد من أن الحجم لا يتجاوز حد تليجرام المسموح (50 ميجابايت)
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            if file_size > 49:
                await msg.edit_text("عذراً، حجم هذا الفيديو أكبر من 50 ميجابايت (الحد الأقصى المسموح للبوتات العادية في تليجرام).")
                os.remove(file_path)
                return

            await msg.edit_text("جاري رفع الفيديو إلى المحادثة... 📤")
            caption_text = "تم التحميل بنجاح ✨\nسبحان الله وبحمده، سبحان الله العظيم 🍃"

            with open(file_path, 'rb') as f:
                await update.message.reply_video(video=f, caption=caption_text)

            if os.path.exists(file_path):
                os.remove(file_path)

            await msg.delete()
        else:
            await msg.edit_text("عذراً، تعذر العثور على صيغة فيديو مناسبة للتنزيل.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text("حدث خطأ أثناء معالجة المقطع. قد يكون الفيديو محميًا أو غير متاح حاليًا.")

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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
