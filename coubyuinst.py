import os
import requests
import argparse
import subprocess
import re
import urllib.parse
import time
import yt_dlp

def download_video(video_url, folder, title, file_format="mp4"):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"{title}.{file_format}")
    if os.path.exists(filename):
        print(f"Skipped (Already downloaded): {filename}")
        return True
    try:
        r = requests.get(video_url, stream=True)
        with open(filename, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Fail: {e}")
        return False

# ----------------- COUB -----------------
def get_coub_items(headers, username=None, item_type="likes", page=1):
    if item_type == "likes":
        url = f"https://coub.com/api/v2/timeline/likes?per_page=50&page={page}"
    else:
        return []
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print("Hata:", r.status_code, r.text[:200])
        return []
    return r.json().get("coubs", [])

def download_coub_likes(session, token):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"{session}; remember_token={token}"
    }
    folder = "coub_likes"
    page = 1
    while True:
        coubs = get_coub_items(headers, item_type="likes", page=page)
        if not coubs:
            break
        for c in coubs:
            title = c["title"] or f"coub_{c['id']}"
            video_url = c["file_versions"]["share"]["default"]
            if video_url:
                download_video(video_url, folder, title.replace("/", "_"))
        page += 1

# ----------------- YOUTUBE -----------------
def download_youtube_video(url, file_format="mp4"):
    import yt_dlp
    folder = "youtube_videos"
    os.makedirs(folder, exist_ok=True)
    if file_format == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': False,
            'nooverwrites': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][vcodec^=avc1][height<=1080]/best[ext=mp4][vcodec^=avc1]',
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': False,
            'nooverwrites': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_youtube_playlist(playlist_url, file_format="mp4"):
    import os
    import yt_dlp
    import traceback
    from datetime import datetime, timezone
    from urllib.parse import urlparse, parse_qs

    folder = "youtube_videos"
    os.makedirs(folder, exist_ok=True)
    debug_file = os.path.join(folder, "youtube-debug.txt")

    # normalize playlist url if user pasted watch?list=...
    parsed = urlparse(playlist_url)
    qs = parse_qs(parsed.query)
    if 'list' in qs:
        real_playlist_id = qs['list'][0]
        playlist_url = f"https://www.youtube.com/playlist?list={real_playlist_id}"

    # Downloader options (used per-video)
    if file_format == "mp3":
        downloader_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(folder, '%(playlist_title)s/%(title)s.%(ext)s'),
            'quiet': False,
            'nooverwrites': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        downloader_opts = {
            'format': 'bestvideo[ext=mp4][vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][vcodec^=avc1][height<=1080]/best[ext=mp4][vcodec^=avc1]',
            'outtmpl': os.path.join(folder, '%(playlist_title)s/%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
            'nooverwrites': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                # yt-dlp expects the misspelled 'preferedformat'
                'preferedformat': 'mp4',
            }],
        }

    # Extractor options: sadece playlist yapısını al, videoların tamamını çözmeye çalışmasın
    extractor_opts = {
        'quiet': False,
        'ignoreerrors': True,        # erişilemeyen/age-restricted entry'leri atla
        'extract_flat': 'in_playlist'  # videoların tam metadata'sını çekme, sadece listeler/ids al
    }

    try:
        extractor = yt_dlp.YoutubeDL(extractor_opts)
        playlist_info = extractor.extract_info(playlist_url, download=False)
    except Exception as e:
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] PLAYLIST-EXTRACTION-ERROR: {playlist_url}\n")
            f.write(f"Error: {str(e)}\n")
            f.write(traceback.format_exc() + "\n\n")
        print(f"Playlist extraction failed: {e}. Logged to {debug_file}")
        return

    entries = playlist_info.get('entries') or []
    total = len(entries)
    print(f"Playlist '{playlist_info.get('title')}' içinde {total} öğe bulundu. İndirme başlıyor...")

    # Her bir entry için tek tek indir
    for idx, entry in enumerate(entries, start=1):
        if not entry:
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] ENTRY NONE: index={idx}\n\n")
            print(f"[{idx}/{total}] Entry None, atlanıyor.")
            continue

        # extract_flat ile gelen entry'de 'url' genellikle video id olabilir; güvenli şekilde url oluştur
        video_id = entry.get('id') or entry.get('url')
        if not video_id:
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] NO-ID: entry={entry}\n\n")
            print(f"[{idx}/{total}] ID yok, atlanıyor.")
            continue

        # video_url oluştur
        if video_id.startswith("http"):
            video_url = video_id
        else:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"[{idx}/{total}] İndiriliyor: {video_url}")

        # her video için yeni downloader örneği (ayrıştırma ve indirme farklı ayarlarla)
        try:
            dl = yt_dlp.YoutubeDL(downloader_opts)
            dl.download([video_url])
        except Exception as e:
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] VIDEO-ERROR: {video_url}\n")
                f.write(f"Flat-title (if present): {entry.get('title')}\n")
                f.write(f"Error: {str(e)}\n")
                f.write(traceback.format_exc() + "\n\n")
            print(f"[{idx}/{total}] Hata: {e}. Detaylar {debug_file} dosyasına yazıldı. Devam ediliyor.")
            continue

    print("İndirme işlemi tamamlandı.")

# ----------------- INSTAGRAM -----------------
# --------- UPDATED Instagram bookmarks downloader ----------

def download_instagram_url(url, out_folder="instagram_videos", format_preference="mp4"):
    """
    Downloads with yt_dlp (public post/igtv/reel).
    format_preference: "mp4" or "mp3"
    """
    import yt_dlp
    os.makedirs(out_folder, exist_ok=True)

    if format_preference == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(out_folder, '%(title)s.%(ext)s'),
            'quiet': False,
            'nooverwrites': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(out_folder, '%(title)s.%(ext)s'),
            'quiet': False,
            'nooverwrites': True,
            'merge_output_format': 'mp4',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"YT-DLP hata ({url}): {e}")
        return False

def download_instagram_from_file(txt_path, out_folder="instagram_videos", format_preference="mp4", cookies_file=None):
    """
    Downloads all videos that indicated per line.
    """
    import yt_dlp
    if not os.path.isfile(txt_path):
        print("Dosya bulunamadı:", txt_path)
        return

    os.makedirs(out_folder, exist_ok=True)

    with open(txt_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    total_urls = 0
    succeeded_urls = 0
    total_items_downloaded = 0

    for index, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not re.match(r'https?://', line):
            print(f"[{index:02d}] Skipped (invalid URL): {line}")
            continue

        total_urls += 1
        print(f"[{index:02d}] Process: {line}")

        # İlk olarak metadata çıkaralım
        ydl_probe_opts = {
            'quiet': True,
            'skip_download': True,
        }
        if cookies_file:
            ydl_probe_opts['cookiefile'] = cookies_file

        try:
            with yt_dlp.YoutubeDL(ydl_probe_opts) as ydl_probe:
                info = None
                try:
                    info = ydl_probe.extract_info(line, download=False)
                except Exception as e:
                    info = None

            items_downloaded_for_url = 0

            if isinstance(info, dict) and info.get('entries'):
                entries = list(info.get('entries') or [])
                for e_index, entry in enumerate(entries, start=1):
                    if not isinstance(entry, dict):
                        continue
                    entry_url = entry.get('webpage_url') or entry.get('original_url') or entry.get('url')
                    if not entry_url:
                        continue

                    is_video = False
                    if entry.get('is_video') is True:
                        is_video = True
                    elif entry.get('formats'):
                        is_video = True
                    elif entry.get('thumbnails') and not entry.get('formats'):
                        is_video = False

                    outtmpl = os.path.join(out_folder, f"{index:02d}-%(playlist_index)s-%(id)s-%(title)s.%(ext)s")

                    if format_preference == "mp3":
                        ydl_opts = {
                            "outtmpl": outtmpl,
                            "noplaylist": True,
                            "cookiefile": cookies_file if cookies_file else None,
                            "format": "bestaudio/best",
                            "postprocessors": [{
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": "192",
                            }],
                            "quiet": False,
                            "nooverwrites": False,
                        }
                    else:
                        fmt = "bestaudio*+bestvideo* / best" if is_video else "bestphoto"
                        ydl_opts = {
                            "outtmpl": outtmpl,
                            "noplaylist": True,
                            "cookiefile": cookies_file if cookies_file else None,
                            "format": fmt,
                            "quiet": False,
                            "nooverwrites": False,
                            "postprocessors": [],
                            "merge_output_format": "mp4",
                        }

                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            print(f"  -> Downloading Carousel ({e_index}/{len(entries)}): {entry_url}")
                            ydl.download([entry_url])
                        items_downloaded_for_url += 1
                        total_items_downloaded += 1
                    except Exception as e:
                        err_msg = f"[{index:02d}] Carousel Download Fail ({entry_url}): {e}"
                        print(err_msg)
                        with open("error_log_01.txt", "a", encoding="utf-8") as f:
                            f.write(err_msg + "\n")
                if items_downloaded_for_url > 0:
                    succeeded_urls += 1

            else:
                is_video = False
                if isinstance(info, dict):
                    if info.get('is_video') is True or info.get('formats'):
                        is_video = True
                    elif info.get('thumbnails') and not info.get('formats'):
                        is_video = False

                outtmpl = os.path.join(out_folder, f"{index:02d}-%(id)s-%(title)s.%(ext)s")

                tried_video_first = False
                did_download = False

                if format_preference == "mp3":
                    ydl_opts = {
                        "outtmpl": outtmpl,
                        "noplaylist": True,
                        "cookiefile": cookies_file if cookies_file else None,
                        "format": "bestaudio/best",
                        "postprocessors": [{
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }],
                        "quiet": False,
                        "nooverwrites": False,
                    }
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([line])
                        did_download = True
                        items_downloaded_for_url += 1
                        total_items_downloaded += 1
                    except Exception as e:
                        err_msg = f"[{index:02d}] MP3 Download Fail ({line}): {e}"
                        print(err_msg)
                        with open("error_log_01.txt", "a", encoding="utf-8") as f:
                            f.write(err_msg + "\n")
                else:
                    video_fmt = "bestaudio*+bestvideo* / best"
                    photo_fmt = "bestphoto"
                    tried_video_first = True
                    ydl_opts_video = {
                        "outtmpl": outtmpl,
                        "noplaylist": True,
                        "cookiefile": cookies_file if cookies_file else None,
                        "format": video_fmt,
                        "quiet": False,
                        "nooverwrites": False,
                        "postprocessors": [],
                        "merge_output_format": "mp4",
                    }
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                            ydl.download([line])
                        did_download = True
                        items_downloaded_for_url += 1
                        total_items_downloaded += 1
                    except Exception as e_video:
                        print(f"[{index:02d}] Video Download Fail: {e_video}")
                        ydl_opts_photo = {
                            "outtmpl": outtmpl,
                            "noplaylist": True,
                            "cookiefile": cookies_file if cookies_file else None,
                            "format": photo_fmt,
                            "quiet": False,
                            "nooverwrites": False,
                        }
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts_photo) as ydl:
                                ydl.download([line])
                            did_download = True
                            items_downloaded_for_url += 1
                            total_items_downloaded += 1
                        except Exception as e_photo:
                            err_msg = f"[{index:02d}] VIDEO/IMG FAIL ({line}): video_err={e_video} | photo_err={e_photo}"
                            print(err_msg)
                            with open("error_log_01.txt", "a", encoding="utf-8") as f:
                                f.write(err_msg + "\n")

                if did_download:
                    succeeded_urls += 1

        except Exception as e_outer:
            err_msg = f"[{index:02d}] Error! ({line}): {e_outer}"
            print(err_msg)
            with open("error_log_01.txt", "a", encoding="utf-8") as f:
                f.write(err_msg + "\n")
            continue

        print(f"[{index:02d}] Download Count: {items_downloaded_for_url}")

        time.sleep(1)

    print(f"Completed: {succeeded_urls}/{total_urls} Downloaded, County: {total_items_downloaded}")

# ----------------- Instagram bookmarks -----------------
# def download_instagram_bookmarks(sessionid, ds_user_id, csrftoken, user_agent):
    # soon

# ----------------- CLI -----------------
if __name__ == "__main__":
        parser = argparse.ArgumentParser(
                description="YouTube, Instagram, Coub Downloader CLI",
                epilog="""
USAGE:
    Download YouTube video (mp4):
        python coubyuinst.py youtube-video --url "https://youtube.com/watch?v=..." --format mp4

    Download YouTube videos as audio (mp3):
        python coubyuinst.py youtube-video --url "https://youtube.com/watch?v=..." --format mp3

    Donwload YouTube playlist (mp4):
        python coubyuinst.py youtube-playlist --url "https://youtube.com/playlist?list=..." --format mp4

    Download YouTube playlist as audio (mp3):
        python coubyuinst.py youtube-playlist --url "https://youtube.com/playlist?list=..." --format mp3

    Download Instagram video:
        python coubyuinst.py instagram-download --url "https://www.instagram.com/p/XXXX/" 

    Download Instagram videos from a URL list (txt file):
        python coubyuinst.py instagram-download --file urls.txt

    Download Coub liked videos:
        python coubyuinst.py coub-likes --session <COUB_SESSION> --token <REMEMBER_TOKEN>
                """,
                formatter_class=argparse.RawDescriptionHelpFormatter
        )

        subparsers = parser.add_subparsers(dest="command", required=True)

        # YouTube video
        yt_video = subparsers.add_parser("youtube-video", help="Download YouTube video (maks 1080p)")
        yt_video.add_argument("--url", required=True, help="YouTube video URL")
        yt_video.add_argument("--format", default="mp4", choices=["mp4", "mp3"], help="format (mp4/mp3)")

        # YouTube playlist
        yt_playlist = subparsers.add_parser("youtube-playlist", help="Donwload YouTube playlist (maks 1080p)")
        yt_playlist.add_argument("--url", required=True, help="YouTube playlist URL")
        yt_playlist.add_argument("--format", default="mp4", choices=["mp4", "mp3"], help="format (mp4/mp3)")

        # Instagram bookmarks (cookie-based) - kept for backward compatibility
        # soon...

        # Instagram download (URL or file)
        insta_dl = subparsers.add_parser("instagram-download", help="Download Instagram video (URL or file)")
        group = insta_dl.add_mutually_exclusive_group(required=True)
        group.add_argument("--url", help="Instagram video/post/reel URL")
        group.add_argument("--file", help="Text file with Instagram URLs (one per line)")
        insta_dl.add_argument("--format", default="mp4", choices=["mp4","mp3"], help="format (mp4/mp3)")
        insta_dl.add_argument("--out", default="instagram_videos", help="Output folder for Instagram videos")

        # Coub likes
        coub = subparsers.add_parser("coub-likes", help="Download Coub liked videos")
        coub.add_argument("--session", required=True, help="_coub_session cookie")
        coub.add_argument("--token", required=True, help="remember_token cookie")

        args = parser.parse_args()

        if args.command == "youtube-video":
            download_youtube_video(args.url, file_format=args.format)
        elif args.command == "youtube-playlist":
            download_youtube_playlist(args.url, file_format=args.format)
        elif args.command == "instagram-bookmarks":
            download_instagram_bookmarks(args.sessionid, args.ds_user_id, args.csrftoken, user_agent=args.user_agent)
        elif args.command == "instagram-download":
            if args.url:
                ok = download_instagram_url(args.url, out_folder=args.out, format_preference=args.format)
                if not ok:
                    print("Failed:", args.url)
            else:
                download_instagram_from_file(args.file, out_folder=args.out, format_preference=args.format)
        elif args.command == "coub-likes":
            download_coub_likes(args.session, args.token)
