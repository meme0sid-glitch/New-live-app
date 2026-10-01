import os
import asyncio
import edge_tts
import requests
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont

# --- Settings ---
YOUTUBE_STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY")
FONT_PATH = "NotoSansDevanagari.ttf" 

async def make_audio(text, output_file):
    # लड़की की असली न्यूज़ एंकर जैसी आवाज़
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
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 800), text[:200] + "...", font=font, fill=(255, 255, 255))
    img.save("temp_bg.png")
    
    audio = AudioFileClip("temp_audio.mp3")
    bg_clip = ImageClip("temp_bg.png").set_duration(audio.duration)
    video = CompositeVideoClip([bg_clip]).set_audio(audio)
    video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')
    print("Video Created!")

def stream_to_youtube(video_path):
    print("Starting Live Stream on YouTube...")
    cmd = f'ffmpeg -re -i {video_path} -c:v libx264 -preset veryfast -b:v 2000k -c:a aac -b:a 128k -f flv rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_STREAM_KEY}'
    os.system(cmd)

if __name__ == "__main__":
    test_script = "नमस्कार, यह एक टेस्ट न्यूज़ है। आज देश में बड़ा बदलाव देखने को मिला है।"
    create_video(test_script, "news_video.mp4")
    stream_to_youtube("news_video.mp4")
