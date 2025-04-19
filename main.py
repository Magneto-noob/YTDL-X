import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.file_id import FileId
from pyrogram import file_id as files
from yt_dlp import YoutubeDL

API_ID = 15523035  # Replace with your API ID
API_HASH = "33a37e968712427c2e7971cb03f341b3"
BOT_TOKEN = "1980052148:AAHk8dLasVYzfDV6A6U0_NxPSTntQax9p1Y"

app = Client("yt_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def format_size(size_bytes):
    if not size_bytes:
        return "?"
    return f"{size_bytes / 1024 / 1024:.1f}MB"

def format_label(fmt):
    ftype = "?"
    if fmt.get("vcodec") != "none" and fmt.get("acodec") != "none":
        ftype = "Video+Audio"
    elif fmt.get("vcodec") != "none":
        ftype = "Video-only"
    elif fmt.get("acodec") != "none":
        ftype = "Audio-only"

    res = f"{fmt.get('height')}p" if fmt.get("height") else f"{fmt.get('abr', '?')}kbps"
    ext = fmt.get("ext", "?")
    size = format_size(fmt.get("filesize"))
    fid = fmt.get("format_id", "?")
    return f"{res} • {ftype} • .{ext} • {size} (ID: {fid})"

def generate_thumbnail(video_path):
    thumb_path = f"{video_path}_thumb.jpg"
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-ss", "00:00:01.000",
            "-vframes", "1", thumb_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return thumb_path if os.path.exists(thumb_path) else None
    except:
        return None

async def send_video_with_meta(client, chat_id, file_path, caption=None, thumb=None):
    try:
        attributes = files.get_file_attributes(file_path)
        duration = int(float(attributes[0].duration or 0))
        width = int(float(attributes[0].w or 0))
        height = int(float(attributes[0].h or 0))
    except Exception:
        duration = width = height = None

    await client.send_video(
        chat_id=chat_id,
        video=file_path,
        caption=caption,
        thumb=thumb if thumb else None,
        supports_streaming=True,
        duration=duration,
        width=width,
        height=height
    )
    

@app.on_message(filters.command("ytdl"))
async def ytdl_handler(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: `/ytdl <YouTube URL>`", quote=True)

    url = message.text.split(None, 1)[1].strip()
    await message.reply("Fetching available formats...")

    try:
        with YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            title = info.get("title", "Video")

        buttons = []
        for fmt in formats:
            if fmt.get("ext") != "mp4":
                continue
            label = format_label(fmt)
            cb_data = f"{fmt['format_id']}|{url}"
            buttons.append([InlineKeyboardButton(label, callback_data=cb_data)])

        if not buttons:
            return await message.reply("No suitable formats found.")

        await message.reply(
            f"Select a format for:\n**{title}**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await message.reply(f"Error: `{e}`")

@app.on_callback_query()
async def download_callback(_, query: CallbackQuery):
    await query.answer()
    format_id, url = query.data.split("|", 1)
    await query.message.edit(f"Downloading format `{format_id}`...")

    try:
        ydl_opts = {
            "format": f"{format_id}+bestaudio/best",
            "outtmpl": "%(title)s.%(ext)s",
            "merge_output_format": "mp4",
            "quiet": True
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)
            title = info.get("title", "Video")

        thumb_path = generate_thumbnail(file_path)

        await send_video_with_meta(
            client=app,
            chat_id=query.message.chat.id,
            file_path=file_path,
            caption=title,
            thumb=thumb_path
        )

        os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)

        await query.message.delete()

    except Exception as e:
        await query.message.edit(f"Download failed: `{e}`")

app.run()
        
