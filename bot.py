import os
import logging
import subprocess
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلا! ابعت فيديو 🎥")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fid = update.message.video.file_id if update.message.video else update.message.document.file_id
    user_data[update.effective_user.id] = {"video": fid}
    await update.message.reply_text("تمام! هلق ابعت الأغنية 🎵")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_data:
        await update.message.reply_text("ابعت فيديو أول!")
        return
    fid = None
    if update.message.audio:
        fid = update.message.audio.file_id
    elif update.message.voice:
        fid = update.message.voice.file_id
    else:
        fid = update.message.document.file_id
    user_data[uid]["audio"] = fid
    await update.message.reply_text("وصلت! هلق ابعت النص ✍️")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_data or "audio" not in user_data[uid]:
        return
    text = update.message.text
    if text.startswith("/"):
        return
    await update.message.reply_text("⏳ عم اشتغل...")
    vp = ""
    ap = ""
    op = ""
    try:
        bot = context.bot
        vf = await bot.get_file(user_data[uid]["video"])
        af = await bot.get_file(user_data[uid]["audio"])
        vp = f"/tmp/{uuid.uuid4()}.mp4"
        ap = f"/tmp/{uuid.uuid4()}.mp3"
        op = f"/tmp/{uuid.uuid4()}.mp4"
        await vf.download_to_drive(vp)
        await af.download_to_drive(ap)
        safe_text = text.replace("'", "").replace(":", "")
        cmd = [
            "ffmpeg", "-y",
            "-i", vp,
            "-i", ap,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            "-vf", f"drawtext=text='{safe_text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontcolor=white:bordercolor=black:borderw=3:x=(w-text_w)/2:y=h-th-60:fontsize=48",
            op
        ]
        subprocess.run(cmd, check=True)
        await update.message.reply_video(video=open(op, 'rb'), caption="تفضل! 🔥")
        if os.path.exists(vp):
            os.remove(vp)
        if os.path.exists(ap):
            os.remove(ap)
        if os.path.exists(op):
            os.remove(op)
        del user_data[uid]
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"خطأ: {e}")
        if vp and os.path.exists(vp):
            os.remove(vp)
        if ap and os.path.exists(ap):
            os.remove(ap)
        if op and os.path.exists(op):
            os.remove(op)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO | filters.DocumentType.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE | filters.DocumentType.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot Live!")
    app.run_polling()

if __name__ == "__main__":
    main()
