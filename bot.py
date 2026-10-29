import os, subprocess, uuid, logging, urllib.request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
user_data = {}

# --- إعدادات نفس صورتك ---
FONT_SIZE = 65  # نفس حجم الكتابة يلي بالصورة - اذا بدك اكبر حط 75
FONT_PATH = "/tmp/aref.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/arefruqaa/ArefRuqaaInk-Bold.ttf"

def ensure_font():
    if not os.path.exists(FONT_PATH):
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        except:
            return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return FONT_PATH

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ابعت فيديو 🌙")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fid = update.message.video.file_id if update.message.video else update.message.document.file_id
    user_data[update.effective_user.id] = {"video": fid}
    await update.message.reply_text("تمام! هلق الأغنية 🎵")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_data: 
        await update.message.reply_text("ابعت فيديو أول!")
        return
    fid = update.message.audio.file_id if update.message.audio else update.message.voice.file_id if update.message.voice else update.message.document.file_id
    user_data[uid]["audio"] = fid
    await update.message.reply_text("هلق ابعت النص سطرين متل:\nجف العود اشتياقاً\nفمتى يزهر اللقاء؟")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_data or "audio" not in user_data[uid]: return
    text = update.message.text
    if text.startswith("/"): return
    await update.message.reply_text("⏳ عم اشتغل بنفس زخرفة صورتك...")
    vp = ap = op = ""
    try:
        font = ensure_font()
        bot = context.bot
        vf = await bot.get_file(user_data[uid]["video"])
        af = await bot.get_file(user_data[uid]["audio"])
        vp = f"/tmp/{uuid.uuid4()}.mp4"
        ap = f"/tmp/{uuid.uuid4()}.mp3"
        op = f"/tmp/{uuid.uuid4()}.mp4"
        await vf.download_to_drive(vp)
        await af.download_to_drive(ap)

        # نحول السطر الثاني لسطر جديد
        safe_text = text.replace("'", "").replace(":", "").strip().replace("\n", "\\n")

        # نفس فلتر صورتك: ليلي غامق + فينيت + نص بالنص مزخرف
        vfilt = f"eq=brightness=-0.08:contrast=1.1:saturation=0.9,vignette=PI/4,drawtext=text='{safe_text}':fontfile={font}:fontcolor=white:fontsize={FONT_SIZE}:shadowcolor=black@0.7:shadowx=2:shadowy=2:x=(w-text_w)/2:y=(h-text_h)/2-80:line_spacing=20"

        cmd = ["ffmpeg","-y","-i",vp,"-i",ap,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-c:a","aac","-shortest","-vf",vfilt,op]
        subprocess.run(cmd, check=True)
        await update.message.reply_video(video=open(op, 'rb'), caption="🌙 نفس زخرفتك جاهزة!")
        for p in [vp,ap,op]:
            if os.path.exists(p): os.remove(p)
        del user_data[uid]
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"خطأ: {e}")
        for p in [vp,ap,op]:
            if p and os.path.exists(p): os.remove(p)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.DocumentType.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.DocumentType.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
