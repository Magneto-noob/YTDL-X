import os
import subprocess
import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL

API_ID = 15523035  # Replace with your API ID
API_HASH = "33a37e968712427c2e7971cb03f341b3"
BOT_TOKEN = "1980052148:AAHk8dLasVYzfDV6A6U0_NxPSTntQax9p1Y"

app = Client("yt_format_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_all_mp4_formats(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
        video_formats = []

        for f in formats:
            if f.get("ext") != "mp4" or not f.get("format_id") or not f.get("height"):
                continue
            size = f.get("filesize") or 0
            mb = f"{size / 1024 / 1024:.1f}MB" if size else "?"
            res = f"{f.get('height')}p"
            video_formats.append({
                "id": f["format_id"],
                "res": res,
                "size": mb
            })

        return info.get("title", "Video"), info.get("id"), video_formats

def generate_thumbnail(video_path, output_path):
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-ss', '00:00:01',
            '-vframes', '1', output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path if os.path.exists(output_path) else None
    except:
        return None

@app.on_message(filters.command("ytdl"))
async def ytdl_handler(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: `/ytdl <YouTube URL>`", quote=True)

    url = message.text.split(None, 1)[1].strip()
    await message.reply("Fetching available formats...")

    try:
        title, video_id, formats = get_all_mp4_formats(url)
        if not formats:
            return await message.reply("No .mp4 formats found.")

        buttons = []
        for f in formats:
            btn_text = f"{f['res']} - {f['size']} (ID: {f['id']})"
            callback_data = f"{f['id']}|{url}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

        await message.reply(
            f"Choose format for:\n**{title}**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await message.reply(f"Error fetching formats: `{e}`")

@app.on_callback_query()
async def download_video(_, query: CallbackQuery):
    await query.answer()
    format_id, url = query.data.split("|", 1)
    await query.message.edit_text(f"Downloading format ID `{format_id}`...")

    try:
        ydl_opts = {
         "format": f"{format_id}+bestaudio",
         "outtmpl": "%(title)s.%(ext)s",
         "merge_output_format": "mp4"
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)
            title = info.get("title", "Video")

        thumb_path = f"{file_path}_thumb.jpg"
        thumb_path = generate_thumbnail(file_path, thumb_path)

        await query.message.reply_video(
            video=file_path,
            thumb=thumb_path if thumb_path else None,
            caption=title,
            supports_streaming=True
        )

        os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)

        await query.message.delete()

    except Exception as e:
        await query.message.edit(f"Download failed:\n`{e}`")

app.run()
