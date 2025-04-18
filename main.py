from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

app = Client("bot", bot_token="YOUR_BOT_TOKEN", api_id=API_ID, api_hash="API_HASH")

@app.on_message(filters.command("ytdl"))
async def ytdl_formats(client, message):
    if len(message.command) < 2:
        return await message.reply("Send a YouTube URL like:\n`/ytdl <url>`", parse_mode="markdown")
    
    url = message.command[1]
    try:
        with YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info["formats"]
            video_id = info["id"]
    except Exception as e:
        return await message.reply(f"Failed to fetch formats:\n{e}")

    buttons = []
    for fmt in formats:
        if not fmt.get("format_note"): continue
        label = f"{fmt['format_note']} ({fmt['ext']})"
        fid = fmt["format_id"]
        buttons.append([InlineKeyboardButton(label, callback_data=f"ytdl:{url}:{fid}")])
    
    await message.reply("Choose a format:", reply_markup=InlineKeyboardMarkup(buttons))

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
    except Exception as e:
        await callback_query.message.edit(f"Download failed:\n{e}")

app.run()
