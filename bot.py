import os
import json
from pyrogram import Client, filters
import instaloader
import requests
import subprocess
from config import API_ID, API_HASH, BOT_TOKEN, RAPIDAPI_KEY, RAPIDAPI_HOST

app = Client("media_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
loader = instaloader.Instaloader()

# Path to the data.json file
USER_DATA_FILE = 'data.json'

class MediaProcessor:
    @staticmethod
    def process_instagram_media(url, prefix='temp'):
        try:
            if "stories" in url or "highlights" in url:
                return MediaProcessor._process_highlights(url, prefix)
            else:
                post = instaloader.Post.from_shortcode(loader.context, url.split("/")[-2])
                media_type = 'video' if post.is_video else 'image'
                download_url = post.video_url if post.is_video else post.url
                ext = {'video': 'mp4', 'image': 'jpg'}.get(media_type, 'media')
                temp_filename = f"{prefix}_media.{ext}"
                with open(temp_filename, 'wb') as f:
                    response = requests.get(download_url, stream=True)
                    if response.status_code != 200:
                        return None
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                if media_type == 'video':
                    return MediaProcessor._validate_video(temp_filename, post.caption or '📸 Instagram Media')
                elif media_type == 'image':
                    return MediaProcessor._validate_image(temp_filename, post.caption or '📸 Instagram Media')
        except:
            return None

    @staticmethod
    def _process_highlights(url, prefix):
        try:
            highlight_id = url.split("/")[-2]
            loader.download_story_highlights(highlight_id, fast_update=True, filename_prefix=prefix)
            files = os.listdir()
            media_files = [{'filename': file, 'type': 'video' if file.endswith('.mp4') else 'image', 'caption': '🎥 Highlight Media'} for file in files if file.startswith(prefix)]
            return media_files
        except:
            return None

    @staticmethod
    def _validate_video(filename, caption):
        video = cv2.VideoCapture(filename)
        width, height, fps = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)), video.get(cv2.CAP_PROP_FPS)
        duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / fps if fps > 0 else 0
        video.release()
        if width == 0 or height == 0 or duration == 0:
            os.remove(filename)
            return None
        return {'filename': filename, 'type': 'video', 'caption': caption, 'duration': int(duration)}

    @staticmethod
    def _validate_image(filename, caption):
        try:
            img = Image.open(filename)
            img.verify()
            width, height = img.size
            if width == 0 or height == 0:
                os.remove(filename)
                return None
            return {'filename': filename, 'type': 'image', 'caption': caption}
        except:
            os.remove(filename)
            return None

    @staticmethod
    def process_snapchat_media(url, prefix='temp'):
        conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
        headers = {'x-rapidapi-key': RAPIDAPI_KEY, 'x-rapidapi-host': RAPIDAPI_HOST}
        conn.request("GET", f"/download?url={url}", headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        video_url = data.get("video_url")
        if video_url:
            temp_filename = f"{prefix}_snapchat.mp4"
            with open(temp_filename, 'wb') as f:
                response = requests.get(video_url, stream=True)
                if response.status_code != 200:
                    return None
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return {'filename': temp_filename, 'type': 'video', 'caption': '🎥 Snapchat Video'}
        return None

def save_user_data(user_info):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    user_id = user_info['chat_id']
    data[user_id] = user_info

    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_info = {
        "name": message.from_user.first_name,
        "username": message.from_user.username,
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
    }

    save_user_data(user_info)

    welcome_msg = f"🎉 Hello {message.from_user.first_name}, welcome to **Media Downloader Pro**! 🚀\n\nI'm here to help you download media from Instagram, Snapchat, YouTube, and more! Just send me a link and I'll take care of the rest. 😎"
    await message.reply_text(welcome_msg)

@app.on_message(filters.regex(r'(instagram\.com/(reel/|p/|stories/|s/aGlnaGxpZ2h0|highlights).*?)'))
async def handle_instagram_url(client, message):
    url = message.text
    processing_msg = await message.reply_text("🔄 Downloading Media...")
    try:
        result = MediaProcessor.process_instagram_media(url)
        await processing_msg.edit_text("📤 Uploading Media...")
        if isinstance(result, list):
            for media_info in result:
                await _send_single_media(client, message, media_info)
        elif result:
            await _send_single_media(client, message, result)
        else:
            await processing_msg.edit_text("❌ Failed to process the Instagram media.")
        await processing_msg.delete()
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

@app.on_message(filters.regex(r'(snapchat\.com/.*)'))
async def handle_snapchat_url(client, message):
    url = message.text
    processing_msg = await message.reply_text("🔄 Downloading Media...")
    try:
        result = MediaProcessor.process_snapchat_media(url)
        await processing_msg.edit_text("📤 Uploading Media...")
        if result:
            await _send_single_media(client, message, result)
        else:
            await processing_msg.edit_text("❌ Failed to process the Snapchat media.")
        await processing_msg.delete()
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

@app.on_message(filters.regex(r'(youtube\.com/.*|youtu\.be/.*)'))
async def handle_youtube_url(client, message):
    url = message.text
    processing_msg = await message.reply_text("🔄 Downloading YouTube Media...")
    try:
        result = subprocess.run(['python3', 'yt.py', url], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            await message.reply_text(output)
        else:
            await message.reply_text("❌ Failed to process the YouTube video.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

async def _send_single_media(client, message, media_info):
    try:
        if media_info['type'] == 'video':
            await client.send_video(chat_id=message.chat.id, video=media_info['filename'], caption=media_info['caption'])
        elif media_info['type'] == 'image':
            await client.send_photo(chat_id=message.chat.id, photo=media_info['filename'], caption=media_info['caption'])
        os.remove(media_info['filename'])
    except:
        await message.reply_text("❌ Could not send media.")

app.run()
