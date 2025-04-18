from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import os

API_ID = 15523035       # your API ID
API_HASH = "33a37e968712427c2e7971cb03f341b3"
BOT_TOKEN = "1980052148:AAHk8dLasVYzfDV6A6U0_NxPSTntQax9p1Y"

app = Client("ytdl-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("ytdl"))
async def ytdl_formats(client, message):
    if len(message.command) < 2:
        return await message.reply("Send a YouTube URL like:\n`/ytdl <url>`", parse_mode="markdown")
    
    url = message.command[1]
    try:
        with YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info["formats"]
    except Exception as e:
        return await message.reply(f"Failed to fetch formats:\n{e}")

    # Build button list for mp4 only
    buttons = []
    for fmt in formats:
        if fmt.get("ext") != "mp4":
            continue
        if not fmt.get("format_note"):
            continue
        label = f"{fmt['format_note']} ({fmt['ext']})"
        fid = fmt["format_id"]
        buttons.append([InlineKeyboardButton(label, callback_data=f"ytdl:{url}:{fid}")])
    
    if not buttons:
        return await message.reply("No .mp4 formats found.")

    await message.reply("Choose an MP4 format to download:", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^ytdl:"))
async def download_selected_format(client, callback_query):
    _, url, format_id = callback_query.data.split(":", 2)
    await callback_query.answer()
    await callback_query.message.edit(f"Downloading format {format_id}...")

    ydl_opts = {
        "format": format_id,
        "outtmpl": f"/tmp/{format_id}-%(title)s.%(ext)s"
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await client.send_document(callback_query.message.chat.id, filename, caption=info["title"])
        os.remove(filename)
    except Exception as e:
        await callback_query.message.edit(f"Download failed:\n{e}")

app.run()
