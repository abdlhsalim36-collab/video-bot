import os, subprocess, uuid, logging, urllib.request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
user_data = {}

FONT_PATH = "/tmp/aref.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/arefruqaa/ArefRuqaaInk-Bold.ttf"

def ensure_font():
    if not os.path.exists(FONT_PATH):
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        except:
            return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return FONT_PATH

async def start(update, context):
    await update.message.reply_text("ابعت فيديو")

async def handle_video(update, context):
    fid = update.message.video.file_id if update.message.video else update.message.document.file_id
    user_data[update.effective_user.id] = {"video": fid}
    await update.message.reply_text("فيديو تمام ✅ هلق ابعت الأغنية")

async def handle_audio(update, context):
    uid = update.effective_user.id
    if uid not in user_data:
        await update.message.reply_text("ابعت فيديو أول!")
        return
    fid = update.message.audio.file_id if update.message.audio else update.message.voice.file_id if update.message.voice else update.message.document.file_id
    user_data[uid]["audio"] = fid
    await update.message.reply_text("أغنية تمام ✅ هلق ابعت النص")

async def handle_text(update, context):
    uid = update.effective_user.id
    if uid not in user_data or "audio" not in user_data[uid]:
        return
    text = update.message.text
    if text.startswith("/"):
        return
    
    await update.message.reply_text("⏳ عم اشتغل...")
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

        safe = text.replace("'", "").replace(":", "").strip().replace("\n", " ")

        # فلتر حلو + خط مزخرف + مكان تحت مثل صورتك
        vfilt = f"eq=contrast=1.08:brightness=0.02:saturation=1.25,unsharp=5:5:0.8:3:3:0.4,drawtext=text='{safe}':fontfile={font}:fontcolor=white:fontsize=58:borderw=7:bordercolor=black@0.85:shadowcolor=black@0.6:shadowx=4:shadowy=4:x=(w-text_w)/2:y=h-th-95"

        cmd = ["ffmpeg","-y","-i",vp,"-i",ap,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-c:a","aac","-shortest","-vf",vfilt,op]
        subprocess.run(cmd, check=True)
        await update.message.reply_video(video=open(op, 'rb'), caption="جاهز 🔥")
        
        for p in [vp, ap, op]:
            if os.path.exists(p):
                os.remove(p)
        del user_data[uid]
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"خطأ: {e}")
        for p in [vp, ap, op]:
            if p and os.path.exists(p):
                os.remove(p)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.DocumentType.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.DocumentType.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
