import telebot, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont
TOKEN = os.getenv("BOT_TOKEN", "9109693800:AAEyApVhtD-nMXxWLnQe7DECyPR0RdQ3uR0")
bot = telebot.TeleBot(TOKEN, threaded=False)
def get_font(sz=48):
 for p in ["./arabic.ttf", "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"]:
  if os.path.exists(p):
   try: return ImageFont.truetype(p, sz)
   except: pass
 return ImageFont.load_default()
def clean(t): return t.replace("🤎","").replace("🤍","").strip()
@bot.message_handler(commands=['start'])
def s(m): bot.reply_to(m, "🔥 البوت شغال 24/7!")
@bot.message_handler(content_types=['video','video_note','animation','document','audio','voice'])
def handle_all(m):
 uid = m.from_user.id
 try:
  if m.content_type in ['audio','voice'] or (m.content_type=='document' and m.document.file_name.lower().endswith(('.mp3','.m4a','.ogg','.wav'))):
   fid = m.audio.file_id if m.content_type=='audio' else m.voice.file_id if m.content_type=='voice' else m.document.file_id
   f = bot.get_file(fid); data = bot.download_file(f.file_path)
   tmp = f"tmp_{uid}"; open(tmp,'wb').write(data)
   mp3 = f"bgm_{uid}.mp3"
   subprocess.run(["ffmpeg","-y","-i",tmp,"-c:a","libmp3lame","-q:a","4",mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
   os.remove(tmp); bot.reply_to(m, "🎵 حفظت الغنية! هلق ابعت النص"); return
  fid = m.video.file_id if m.content_type=='video' else m.video_note.file_id if m.content_type=='video_note' else m.animation.file_id if m.content_type=='animation' else m.document.file_id
  f = bot.get_file(fid); data = bot.download_file(f.file_path)
  raw = f"raw_{uid}.mp4"; open(raw,'wb').write(data)
  out = f"in_{uid}.mp4"
  subprocess.run(["ffmpeg","-y","-i",raw,"-vf","scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2","-c:v","libx264","-preset","ultrafast","-r","30","-c:a","aac",out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  if os.path.exists(raw): os.remove(raw)
  bot.reply_to(m, "✅ حفظت الفيديو! ابعت النص")
 except Exception as e: bot.reply_to(m, f"خطأ: {e}")
@bot.message_handler(content_types=['text'])
def txt_handler(m):
 if m.text.startswith('/'): return
 uid = m.from_user.id; in_path = f"in_{uid}.mp4"
 if not os.path.exists(in_path): bot.reply_to(m, "ابعت فيديو أول!"); return
 bot.reply_to(m, "🎬 عم ركب...")
 try:
  txt = clean(m.text); W,H = 720,1280
  img = Image.new('RGBA',(W,H),(0,0,0,0)); d = ImageDraw.Draw(img); font = get_font(48); y = int(H*0.75)
  for line in textwrap.wrap(txt,width=22):
   bb = d.textbbox((0,0),line,font=font,stroke_width=7); x = (W-(bb[2]-bb[0]))//2
   d.text((x,y),line,font=font,fill='white',stroke_width=7,stroke_fill='black'); y+=70
  txt_path = f"txt_{uid}.png"; img.save(txt_path)
  out_path = f"out_{uid}.mp4"; bgm = f"bgm_{uid}.mp3"
  has_music = os.path.exists(bgm) and os.path.getsize(bgm) > 1000
  if has_music:
   cmd = ["ffmpeg","-y","-i",in_path,"-i",txt_path,"-i",bgm,"-filter_complex","[0:v][1:v]overlay=0:0[v];[0:a][2:a]amix=inputs=2:duration=shortest[a]","-map","[v]","-map","[a]","-c:v","libx264","-preset","ultrafast","-c:a","aac","-shortest",out_path]
  else:
   cmd = ["ffmpeg","-y","-i",in_path,"-i",txt_path,"-filter_complex","[0:v][1:v]overlay=0:0","-c:v","libx264","-preset","ultrafast","-c:a","copy",out_path]
  subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  bot.send_video(m.chat.id, open(out_path,'rb'), caption="✅ جاهز 24/7!")
  for f in [txt_path, out_path]:
   if os.path.exists(f): os.remove(f)
 except Exception as e: bot.reply_to(m, f"خطأ: {e}")
bot.infinity_polling(none_stop=True)
