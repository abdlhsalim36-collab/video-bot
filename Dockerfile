FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg curl fonts-dejavu && rm -rf /var/lib/apt/lists/*
RUN curl -L -o /usr/share/fonts/truetype/DejaVuSans.ttf https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf || true
RUN pip install --no-cache-dir pyTelegramBotAPI Pillow
WORKDIR /app
COPY . .
RUN curl -L -o ./arabic.ttf https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf || echo "no font"
CMD ["python", "bot.py"]
