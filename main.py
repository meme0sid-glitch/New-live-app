import os
import asyncio
import edge_tts
import requests
import zipfile
import threading
import time
import imageio_ffmpeg
import subprocess
from flask import Flask
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
from moviepy.config import change_settings

# --- FFmpeg Setup for Render ---
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
change_settings({"FFMPEG_BINARY": ffmpeg_path})
os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path

# --- Render Web Service के लिए नकली वेबसाइट ---
app = Flask(__name__)

@app.route('/')
def home():
    return "News Live Stream is running in the background..."

# --- Font Auto-Extract Function ---
def ensure_font():
    if not os.path.exists("NotoSansDevanagari.ttf") and os.path.exists("Noto_Sans_Devanagari.zip"):
        print("Extracting Font from ZIP...")
        try:
            with zipfile.ZipFile("Noto_Sans_Devanagari.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith(".ttf"):
                        os.rename(os.path.join(root, file), "NotoSansDevanagari.ttf")
                        print("Font extracted successfully!")
                        return
        except Exception as e:
            print(f"Font extraction failed: {e}")

ensure_font()

# --- Settings ---
YOUTUBE_STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY")
FONT_PATH = "NotoSansDevanagari.ttf" 

async def make_audio(text, output_file):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural", rate="+20%")
    await communicate.save(output_file)

def create_video(text, output_video):
    print("Creating Audio...")
    asyncio.run(make_audio(text, "temp_audio.mp3"))
    
    print("Creating Video...")
    img = Image.new('RGB', (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 50)
    except Exception as e:
        print(f"Font error: {e}")
        font = ImageFont.load_default()
    
    draw.text((50, 800), text[:200] + "...", font=font, fill=(255, 255, 255))
    img.save("temp_bg.png")
    
    audio = AudioFileClip("temp_audio.mp3")
    bg_clip = ImageClip("temp_bg.png").set_duration(audio.duration)
    video = CompositeVideoClip([bg_clip]).set_audio(audio)
    video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')
    print("Video Created!")

def stream_to_youtube(video_path):
    if not YOUTUBE_STREAM_KEY or YOUTUBE_STREAM_KEY == "Testing":
        print("Stream Key is missing or 'Testing'. Skipping live stream.")
        return
        
    print("Starting Live Stream on YouTube...")
    # सीधे subprocess से FFmpeg चलाना (ज्यादा स्टेबल)
    ffmpeg_cmd = [
        ffmpeg_path,
        "-re",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2000k",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        f"rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_STREAM_KEY}"
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(10)  # स्ट्रीम शुरू होने का इंतज़ार
    process.terminate()
    print("Stream command executed.")

def run_streaming_loop():
    while True:
        try:
            test_script = "नमस्कार, यह एक टेस्ट न्यूज़ है। आज देश में बड़ा बदलाव देखने को मिला है।"
            create_video(test_script, "news_video.mp4")
            stream_to_youtube("news_video.mp4")
        except Exception as e:
            print(f"Error in streaming loop: {e}")
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_streaming_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
