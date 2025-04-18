import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL

API_ID = 1234567  # replace with your API_ID
API_HASH = "your_api_hash"  # replace with your API_HASH
BOT_TOKEN = "your_bot_token"  # replace with your BOT_TOKEN

app = Client("ytdl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Get only .mp4 formats
def get_mp4_formats(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        mp4_formats = [f for f in formats if f.get('ext') == 'mp4' and f.get('format_id') and f.get('filesize')]
        return info.get('title'), mp4_formats

# Start command
@app.on_message(filters.command("start"))
async def start_handler(_, message: Message):
    await message.reply("Send a YouTube link using /ytdl <url>")

# /ytdl <url>
@app.on_message(filters.command("ytdl"))
async def ytdl_handler(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply("Send the command like: `/ytdl <url>`")
    
    url = message.text.split(None, 1)[1].strip()
    
    try:
        title, mp4_formats = get_mp4_formats(url)
    except Exception as e:
        return await message.reply(f"Failed to fetch formats: `{e}`")
    
    if not mp4_formats:
        return await message.reply("No .mp4 formats found.")

    buttons = []
    for f in mp4_formats:
        fid = f["format_id"]
        size_mb = round(f["filesize"] / 1024 / 1024, 1)
        buttons.append([InlineKeyboardButton(f"{fid} - {size_mb}MB", callback_data=f"{url}|{fid}")])

    await message.reply(
        f"Choose quality for:\n**{title}**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Callback: download using selected format
@app.on_callback_query()
async def download_callback(_, query: CallbackQuery):
    await query.answer()

    try:
        data = query.data
        url, format_id = data.split("|")
        temp_msg = await query.message.reply(f"Downloading `{format_id}` from YouTube...")

        ydl_opts = {
            "format": format_id,
            "outtmpl": "downloads/%(title)s.%(ext)s",
        }

        os.makedirs("downloads", exist_ok=True)

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.download([url])

        downloaded_files = os.listdir("downloads")
        if not downloaded_files:
            return await temp_msg.edit("Download failed or file not found.")
        
        file_path = os.path.join("downloads", downloaded_files[0])
        await query.message.reply_video(video=file_path, caption="Here’s your video")
        os.remove(file_path)
        await temp_msg.delete()

    except Exception as e:
        await query.message.reply(f"Error: `{e}`")

# Run bot
app.run()
