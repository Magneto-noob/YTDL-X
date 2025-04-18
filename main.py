import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

API_ID = 15523035  # replace with your API ID
API_HASH = "33a37e968712427c2e7971cb03f341b3"
BOT_TOKEN = "1980052148:AAHk8dLasVYzfDV6A6U0_NxPSTntQax9p1Y"

app = Client("yt_format_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_progressive_mp4_formats(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'force_generic_extractor': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        filtered = []
        for fmt in formats:
            if (
                fmt.get('ext') == 'mp4'
                and fmt.get('acodec') != 'none'
                and fmt.get('vcodec') != 'none'
                and fmt.get('format_id')
            ):
                size = fmt.get('filesize') or 0
                mb = f"{size / (1024 * 1024):.2f} MB" if size else "N/A"
                res = fmt.get('height', 'N/A')
                filtered.append({
                    "id": fmt["format_id"],
                    "res": f"{res}p",
                    "size": mb,
                })
        return filtered

@app.on_message(filters.command("ytdl"))
async def ytdl_handler(client, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply("Usage: `/ytdl <YouTube URL>`", quote=True)

    url = message.text.split(None, 1)[1].strip()

    await message.reply("Fetching available formats...")

    try:
        formats = get_progressive_mp4_formats(url)
        if not formats:
            return await message.reply("No progressive .mp4 formats found.")

        buttons = []
        for fmt in formats:
            btn_text = f"{fmt['res']} - {fmt['size']} (ID: {fmt['id']})"
            callback_data = f"{fmt['id']}|{url}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

        await message.reply(
            "Select a format to download:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await message.reply(f"Error: {e}")

@app.on_callback_query()
async def format_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    if "|" not in data:
        return await callback_query.answer("Invalid format.", show_alert=True)

    format_id, url = data.split("|", 1)
    await callback_query.message.edit("Downloading selected format...")

    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file_path = ydl.prepare_filename(info)

        # Download YouTube thumbnail
        video_id = info.get("id")
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        thumb_path = f"{video_id}_thumb.jpg"
        try:
            r = requests.get(thumbnail_url)
            if r.ok:
                with open(thumb_path, "wb") as f:
                    f.write(r.content)
            else:
                thumb_path = None
        except:
            thumb_path = None

        await client.send_video(
            chat_id=callback_query.message.chat.id,
            video=file_path,
            caption=info.get('title', 'Downloaded'),
            supports_streaming=True,
            thumb=thumb_path if thumb_path else None
        )

        os.remove(file_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)

        await callback_query.message.delete()

    except Exception as e:
        await callback_query.message.edit(f"Download failed: {e}")

app.run()
