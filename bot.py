import discord
from discord.ext import commands, tasks
import os
import wave
import pyaudio
import asyncio
from discord import FFmpegPCMAudio
import nacl
import nacl.encoding

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

voice_client = None
audio_file_path = '/Users/garrypotter/Documents/1/'
audio_stream = None
stream = None
frames = []

# Створення директорії для збереження файлів
os.makedirs(audio_file_path, exist_ok=True)

# Команда для запуску моніторингу
@bot.command()
async def вкл(ctx):
    monitor_voice_channel.start()
    await ctx.send("Моніторинг запущено!")

# Команда для зупинки моніторингу
@bot.command()
async def викл(ctx):
    monitor_voice_channel.stop()
    await ctx.send("Моніторинг зупинено!")

@tasks.loop(seconds=5)
async def monitor_voice_channel():
    global voice_client

    # Отримуємо всі активні голосові канали
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            if len(channel.members) >= 2:
                if voice_client is None:
                    voice_client = await channel.connect()
                    start_recording(voice_client)
            elif len(channel.members) < 2:
                if voice_client is not None:
                    await voice_client.disconnect()
                    stop_recording()
                    voice_client = None

def start_recording(client):
    """Починає запис аудіо потоку"""
    global audio_stream, stream, frames

    os.makedirs(audio_file_path, exist_ok=True)
    audio_file = wave.open(os.path.join(audio_file_path, "output.wav"), 'wb')
    audio_file.setnchannels(1)  # Моно
    audio_file.setsampwidth(2)  # 16 біт
    audio_file.setframerate(44100)  # Частота дискретизації

    # Створюємо аудіо потік для запису
    audio_stream = pyaudio.PyAudio()
    stream = audio_stream.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    frames = []  # Очищаємо попередні записи

    # Додаємо функцію запису
    def record_audio():
        try:
            while True:
                data = stream.read(1024)
                frames.append(data)
        except KeyboardInterrupt:
            pass  # Для безпечного завершення запису

    # Стартуємо запис в окремому потоці
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, record_audio)

def stop_recording():
    """Зупиняє запис та коректно закриває файл"""
    global frames, stream, audio_stream

    if frames:
        # Записуємо всі зібрані фрейми в файл
        audio_file = wave.open(os.path.join(audio_file_path, "output.wav"), 'wb')
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(44100)
        audio_file.writeframes(b''.join(frames))
        audio_file.close()

    # Закриваємо потік аудіо
    if stream is not None:
        stream.stop_stream()
        stream.close()

    if audio_stream is not None:
        audio_stream.terminate()

    frames = []  # Очищаємо зібрані фрейми

bot.run('YOUR_DISCORD_BOT_TOKEN')