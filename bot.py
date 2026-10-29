import os, asyncio, tempfile, threading, http.server, socketserver
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import subprocess

# حل مشكلة البورت ل Render
def keep_alive():
    try:
        port = int(os.environ.get("PORT", 10000))
        socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=keep_alive, daemon=True).start()

TOKEN = os.environ.get("BOT_TOKEN")
user_data = {}

def run_ffmpeg(cmd):
    subprocess.run(cmd, check=True)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.video.get_file() if update.message.video else await update.message.document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
        await file.download_to_drive(tf.name)
        user_data[update.effective_user.id] = {"video": tf.name, "audio": user_data.get(update.effective_user.id, {}).get("audio"), "text": user_data.get(update.effective_user.id, {}).get("text")}
    await update.message.reply_text("✅ الفيديو انحفظ! هلق ابعت الأغنية، وبعدها النص")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.audio.get_file() if update.message.audio else await update.message.voice.get_file() if update.message.voice else await update.message.document.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
        await file.download_to_drive(tf.name)
        d = user_data.get(update.effective_user.id, {})
        d["audio"] = tf.name
        user_data[update.effective_user.id] = d
    await update.message.reply_text("✅ الأغنية انحفظت! هلق ابعت النص")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("/"): return
    uid = update.effective_user.id
    d = user_data.get(uid, {})
    if "video" not in d:
        await update.message.reply_text("ابعت فيديو أول شي!")
        return
    d["text"] = text
    user_data[uid] = d
    
    if "audio" not in d:
        await update.message.reply_text("✅ النص انحفظ! هلق ابعت الأغنية")
        return

    await update.message.reply_text("⏳ عم اشتغل على الفيديو... ثواني")

    try:
        video_path = d["video"]
        audio_path = d["audio"]
        txt = d["text"]

        # إزالة صوت الفيديو الأصلي + تجهيز الفيديو بدون صوت
        no_audio_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        run_ffmpeg(["ffmpeg", "-y", "-i", video_path, "-an", "-c:v", "copy", no_audio_video])
        
        # إضافة النص بتصميم فخم
        with_text = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        # خط أبيض فخم بحدود سوداء في النص السفلي
        drawtext = f"drawtext=text='{txt}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontcolor=white:fontsize=48:borderw=4:bordercolor=black:x=(w-text_w)/2:y=h-th-100"
        run_ffmpeg(["ffmpeg", "-y", "-i", no_audio_video, "-vf", drawtext, "-c:a", "copy", with_text])

        # دمج الصوت الجديد فقط
        final_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        run_ffmpeg(["ffmpeg", "-y", "-i", with_text, "-i", audio_path, "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", final_path])

        await update.message.reply_video(video=open(final_path, "rb"), caption="🔥 جاهز!")
        
        for p in [video_path, audio_path, no_audio_video, with_text, final_path]:
            try: os.remove(p)
            except: pass
        user_data.pop(uid, None)

    except Exception as e:
        await update.message.reply_text(f"صار خطأ: {e}")
        print(e)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.VIDEO | (filters.Document.VIDEO), handle_video))
app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | (filters.Document.AUDIO), handle_audio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Bot started!")
app.run_polling()
