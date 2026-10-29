FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyTelegramBotAPI Pillow
WORKDIR /app
COPY . .
RUN curl -L -o ./arabic.ttf https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf
CMD ["python", "bot.py"]
