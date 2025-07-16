
# 🎧 Media Downloader App with Instagram Fallback & FFmpeg Check

import streamlit as st
import yt_dlp
import os
from pathlib import Path
import subprocess

st.set_page_config(page_title="🎧 Media Downloader", layout="centered")
st.title("🎧 Media Downloader")

mode = st.radio("Select Mode", ["🔍 YouTube Search", "📎 Paste URL"])
download_type = st.selectbox("Download as", ["MP4 (Video)", "MP3 (Audio)"])
cookies_file = st.file_uploader("Optional: Upload Instagram cookies.txt", type="txt")

def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def get_cookies_path():
    if cookies_file:
        path = Path("cookies.txt")
        path.write_bytes(cookies_file.read())
        return str(path)
    return None

def download_video_or_audio(url, audio=False, cookies_path=None):
    if not check_ffmpeg_installed():
        return None, "❌ FFmpeg is not installed. Please install FFmpeg and add it to your system PATH."

    output_format = "downloaded_audio.%(ext)s" if audio else "downloaded_video.%(ext)s"
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if not audio else 'bestaudio/best',
        'merge_output_format': 'mp4' if not audio else 'mp3',
        'outtmpl': output_format,
        'quiet': True,
        'noplaylist': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if audio else [],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        },
    }

    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"
            return info, file_path
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if "ffmpeg" in error_msg:
            return None, "❌ FFmpeg is required but not installed. Please install FFmpeg and try again."
        if "login required" in error_msg or "cookies" in error_msg or "rate-limit" in error_msg:
            help_msg = (
                "⚠️ Instagram login required or rate-limit hit.

"
                "👉 To fix this, please upload a `cookies.txt` file.
"
                "1. Use [this Chrome Extension](https://chrome.google.com/webstore/detail/get-cookiestxt/lopibhbgjfomkbcbekacimigcfpbnfcb)
"
                "2. Login to [instagram.com](https://instagram.com)
"
                "3. Click the extension and download cookies.txt
"
                "4. Upload it here using the uploader above ⬆️"
            )
            return None, help_msg
        return None, f"❌ Download failed: {e}"

# 📎 Paste URL or Search YouTube
if mode == "📎 Paste URL":
    input_text = st.text_input("🔍 Paste YouTube/Instagram URL or Search YouTube", placeholder="Paste link or search...")
    if st.button("Search or Download"):
        if input_text:
            if input_text.startswith("http://") or input_text.startswith("https://"):
                with st.spinner("⏬ Downloading..."):
                    cookies_path = get_cookies_path()
                    is_audio = (download_type == "MP3 (Audio)")
                    info, result = download_video_or_audio(input_text, audio=is_audio, cookies_path=cookies_path)

                if info:
                    st.success("✅ Download Complete!")
                    st.write("🎬 Title:", info.get("title"))
                    st.write("📺 Uploader:", info.get("uploader"))
                    media_display = st.audio if is_audio else st.video
                    media_display(result)
                    with open(result, 'rb') as f:
                        st.download_button(f"⬇️ Download {download_type}", f, file_name=os.path.basename(result))
                    os.remove(result)
                else:
                    st.warning(result)

            else:
                with st.spinner("🔍 Searching YouTube..."):
                    try:
                        ydl_opts = {
                            'quiet': True,
                            'extract_flat': True,
                            'skip_download': True,
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            result = ydl.extract_info(f"ytsearch5:{input_text}", download=False)
                            videos = result['entries']
                        st.subheader("Search Results")
                        for video in videos:
                            st.markdown(f"**{video['title']}**")
                            if st.button(f"Download '{video['title']}' as {download_type}", key="search_" + video['id']):
                                with st.spinner("⏬ Downloading..."):
                                    video_url = f"https://www.youtube.com/watch?v={video['id']}"
                                    info, file_path = download_video_or_audio(video_url, audio=(download_type == "MP3 (Audio)"))
                                if info:
                                    st.success("✅ Download Complete!")
                                    media_display = st.audio if download_type == "MP3 (Audio)" else st.video
                                    media_display(file_path)
                                    with open(file_path, 'rb') as f:
                                        st.download_button(f"⬇️ Download {download_type}", f, file_name=os.path.basename(file_path))
                                    os.remove(file_path)
                                else:
                                    st.warning(file_path)
                    except Exception as e:
                        st.error(f"Search failed: {e}")

# 🔍 YouTube Search Mode
elif mode == "🔍 YouTube Search":
    query = st.text_input("Search YouTube", placeholder="Type a song or video name")
    if query:
        with st.spinner("🔍 Searching..."):
            try:
                ydl_opts = {
                    'quiet': True,
                    'extract_flat': True,
                    'skip_download': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(f"ytsearch5:{query}", download=False)
                    videos = result['entries']
                st.subheader("Search Results")
                for video in videos:
                    st.markdown(f"**{video['title']}**")
                    if st.button(f"Download '{video['title']}' as {download_type}", key=video['id']):
                        with st.spinner("⏬ Downloading..."):
                            video_url = f"https://www.youtube.com/watch?v={video['id']}"
                            info, file_path = download_video_or_audio(video_url, audio=(download_type == "MP3 (Audio)"))
                        if info:
                            st.success("✅ Download Complete!")
                            media_display = st.audio if download_type == "MP3 (Audio)" else st.video
                            media_display(file_path)
                            with open(file_path, 'rb') as f:
                                st.download_button(f"⬇️ Download {download_type}", f, file_name=os.path.basename(file_path))
                            os.remove(file_path)
                        else:
                            st.warning(file_path)
            except Exception as e:
                st.error(f"Search failed: {e}")
