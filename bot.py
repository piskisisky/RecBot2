import discord
from discord.ext import commands
import asyncio
import os
import subprocess
from datetime import datetime

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
    raise ValueError("Токен бота не знайдено у змінних середовища!")

# Створення тимчасової папки для зберігання записів
temp_dir = '/tmp/recordings'
os.makedirs(temp_dir, exist_ok=True)

# Шлях до файлу
audio_file_path = os.path.join(temp_dir, 'audio_recording.wav')

# Запис аудіо в файл
def save_audio_file(audio_data):
    with open(audio_file_path, 'wb') as f:
        f.write(audio_data)
    print(f"Audio saved to {audio_file_path}")

# Приклад виклику функції з даними аудіо
audio_data = b"dummy_audio_data"  # Це має бути твій реальний аудіо потік
save_audio_file(audio_data)

intents = discord.Intents.default()
intents.voice_states = True  # Важливо для відстеження голосових каналів

bot = commands.Bot(command_prefix="!", intents=intents)

voice_clients = {}  # Зберігаємо активні сесії запису


async def start_recording(vc, channel_id):
    """Функція запису аудіо з голосового каналу через FFmpeg"""
    filename = f"{RECORDINGS_DIR}/recording_{channel_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp3"

    # Запускаємо FFmpeg для запису аудіо
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-f", "s16le",
            "-ar", "48000",
            "-ac", "2",
            "-i", "pipe:0",
            filename
        ],
        stdin=subprocess.PIPE
    )

    voice_clients[channel_id] = (vc, process)
    print(f"🎙️ Почав запис у {filename}")

    return filename


async def stop_recording(channel_id):
    """Зупиняє запис та виходить з голосового каналу"""
    if channel_id in voice_clients:
        vc, process = voice_clients[channel_id]

        # Завершуємо процес ffmpeg
        process.stdin.close()
        process.wait()

        # Виходимо з голосового каналу
        await vc.disconnect()
        del voice_clients[channel_id]

        print(f"🛑 Запис у каналі {channel_id} завершено та збережено.")

        
@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущено та моніторить голосові канали!")


@bot.event
async def on_voice_state_update(member, before, after):
    """Моніторинг кількості учасників у голосових каналах"""
    if member.bot:
        return  # Ігноруємо бота

    channel = after.channel or before.channel  # Знаходимо активний канал

    if not channel:
        return

    # Перевіряємо кількість людей у голосовому каналі
    num_members = sum(1 for m in channel.members if not m.bot)

    if num_members >= 2 and channel.id not in voice_clients:
        # Підключаємось та починаємо запис
        vc = await channel.connect()
        await start_recording(vc, channel.id)

    elif num_members < 2 and channel.id in voice_clients:
        # Завершуємо запис, якщо залишився один користувач
        await stop_recording(channel.id)


@bot.command()
async def start(ctx):
    """Команда для ручного запуску моніторингу"""
    await ctx.send("🎙️ Бот запущено та моніторить голосові чати!")

@bot.command()
async def stop(ctx):
    """Команда для зупинки бота"""
    for channel_id in list(voice_clients.keys()):
        await stop_recording(channel_id)

    await ctx.send("🛑 Бот зупинився та завершив усі записи.")
    await bot.close()


bot.run(TOKEN)
