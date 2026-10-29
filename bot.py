import telebot, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN", "9109693800:AAE...")
bot = telebot.TeleBot(TOKEN, threaded=False)

def get_font(sz=52):
    # بيحاول يلاقي خط عربي مزخرف
    for p in ["./arabic.ttf", "./Amiri-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except:
                pass
    return ImageFont.load_default()

def clean(t):
    return t.replace("❤️","").strip()

@bot.message_handler(commands=['start'])
def s(m):
    bot.reply_to(m, "🔥 البوت شغال 24/7 ! ابعت فيديو ثم غنية ثم النص")

@bot.message_handler(content_types=['video', 'audio', 'voice', 'document'])
def handle_all(m):
    uid = m.from_user.id
    try:
        # اذا غنية
        if m.content_type in ['audio', 'voice'] or (m.document and 'audio' in m.document.mime_type):
            fid = m.audio.file_id if m.content_type=='audio' else m.voice.file_id if m.content_type=='voice' else m.document.file_id
            f = bot.get_file(fid)
            data = bot.download_file(f.file_path)
            tmp = f"tmp_{uid}"
            open(tmp,'wb').write(data)
            mp3 = f"bgm_{uid}.mp3"
            subprocess.run(["ffmpeg","-y","-i",tmp,"-c:a","libmp3lame",mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(tmp)
            bot.reply_to(m, "🎵 تمام حفظت الغنية! هلق ابعت النص")
            return

        # اذا فيديو
        fid = m.video.file_id
        f = bot.get_file(fid)
        data = bot.download_file(f.file_path)
        raw = f"raw_{uid}.mp4"
        open(raw,'wb').write(data)
        out = f"in_{uid}.mp4"
        # الحل هنا: -an بتحذف صوت الفيديو الأصلي نهائياً
        subprocess.run(["ffmpeg","-y","-i",raw,"-vf","scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280","-an","-c:v","libx264","-preset","veryfast",out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(raw):
            os.remove(raw)
        bot.reply_to(m, "✅ حفظت الفيديو بدون صوت! ابعت النص")
    except Exception as e:
        bot.reply_to(m, f"خطأ: {e}")

@bot.message_handler(content_types=['text'])
def txt_handler(m):
    if m.text.startswith('/'):
        return
    uid = m.from_user.id
    in_path = f"in_{uid}.mp4"
    if not os.path.exists(in_path):
        bot.reply_to(m, "📹 ابعت فيديو أول شي")
        return
    bot.reply_to(m, "🎬 عم ركب الفيديو... استنى شوي")
    try:
        txt = clean(m.text)
        W,H = 720,1280
        font = get_font(58)
        img = Image.new('RGBA',(W,H),(0,0,0,0))
        d = ImageDraw.Draw(img)
        lines = textwrap.wrap(txt,width=20)
        total_h = 0
        bboxes = []
        for l in lines:
            bb = d.textbbox((0,0),l,font=font,stroke_width=6)
            bboxes.append(bb)
            total_h += (bb[3]-bb[1]) + 20
        y = (H - total_h)//2
        for i, line in enumerate(lines):
            bb = bboxes[i]
            x = (W - (bb[2]-bb[0]))//2
            d.text((x,y),line,font=font,fill='white',stroke_width=6,stroke_fill='black')
            y += (bb[3]-bb[1]) + 20
        txt_path = f"txt_{uid}.png"
        img.save(txt_path)
        out_path = f"out_{uid}.mp4"
        bgm = f"bgm_{uid}.mp3"
        has_music = os.path.exists(bgm) and os.path.getsize(bgm)>1000
        if has_music:
            cmd = ["ffmpeg","-y","-i",in_path,"-i",txt_path,"-i",bgm,"-filter_complex","[0:v][1:v]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]","-map","[v]","-map","2:a","-c:v","libx264","-c:a","aac","-shortest","-movflags","+faststart",out_path]
        else:
            cmd = ["ffmpeg","-y","-i",in_path,"-i",txt_path,"-filter_complex","[0:v][1:v]overlay=(W-w)/2:(H-h)/2,format=yuv420p","-c:v","libx264","-an","-movflags","+faststart",out_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        bot.send_video(m.chat.id, open(out_path,'rb'), caption="✨ جاهز! صوت الفيديو الأصلي انحذف")
        for f in [txt_path, out_path]:
            if os.path.exists(f):
                os.remove(f)
    except Exception as e:
        bot.reply_to(m, f"خطأ: {e}")

bot.infinity_polling(none_stop=True)
