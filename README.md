# SnapStream - YouTube, Instagram, Coub Video Downloader for Personal Use

A basic Python-based CLI tool designed for personal media archival from YouTube, Instagram, and Coub. 

SnapStream provides basic usage for downloading videos, extracting audio, and managing personal content collections with support for various formats, authentication methods, and batch processing capabilities.

leverages the power of `yt-dlp` (a fork of youtube-dl) and custom API implementations to help users download and organize their favorite content from multiple social media platforms.

### Platform Support
- **YouTube**: Single videos and entire playlists with quality control (max 1080p) in mp4 or mp3 formats
- **Instagram**: Posts, Reels, IGTV, and Bookmark videos
- **Coub**: Entire Liked content with session-based authentication

### Format Flexibility
- **Video Downloads**: MP4 format with optimized encoding (H.264/AVC1 codec preference) (max 1080p)
- **Audio Extraction**: High-quality MP3 conversion (192 kbps) from any video source
- **Batch Processing**: Process multiple URLs from text files

### Advanced Features
- Cookie-based authentication for private content
- Skips already downloaded files to avoid duplicates
- Comprehensive error logging with fallback mechanisms
- Maintains original titles and organizing folder structures
- Real-time download progress and status reporting

### Requirements
It works wherever you can run Python via CLI. But you need to setup a basic workflow environment with following
- **Python**: Version 3.8 or higher (3.9+ recommended for optimal performance)
- **FFmpeg**: Required for audio/video processing and format conversion
- **Internet Connection**: Stable broadband connection for reliable downloads

## Installation & Environment Setup

### Step 1: Python Environment Preparation

First, ensure you have Python 3.8+ installed on your system. You can verify this by opening a terminal or command prompt and running:

```bash
python --version
# or on some systems
python3 --version
```

### Step 2: Create Virtual Environment (Recommended)

Creating a virtual environment isolates your project dependencies and prevents conflicts with other Python projects:

```bash
# Create a new virtual environment
python -m venv coubyuinst-env

# Activate the virtual environment
# On Windows:
coubyuinst-env\Scripts\activate

# On macOS/Linux:
source coubyuinst-env/bin/activate
```

### Step 3: Install Required Python Packages

The script requires several Python packages. Install them using pip:

```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install core dependencies
pip install requests
pip install yt-dlp
pip install argparse  # Usually included with Python

# Optional but recommended for better performance
pip install urllib3
pip install certifi
```

### Step 4: FFmpeg Installation

FFmpeg is crucial for audio/video processing. The installation method varies by operating system:

#### Windows FFmpeg Installation
1. Download FFmpeg from [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Choose "Windows builds by BtbN" for the latest stable version
3. Extract the downloaded archive to `C:\ffmpeg`
4. Add `C:\ffmpeg\bin` to your system PATH environment variable
5. Verify installation: Open Command Prompt and run `ffmpeg -version`

#### macOS FFmpeg Installation
Using Homebrew (recommended):
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FFmpeg
brew install ffmpeg
```

#### Linux FFmpeg Installation
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL/Fedora
sudo yum install ffmpeg
# or for newer versions
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

### Step 5: Download and Setup the Script

1. Download the `coubyuinst.py` file to your desired directory
2. Make sure the file has execution permissions (Linux/macOS):
   ```bash
   chmod +x coubyuinst.py
   ```

### Step 6: Verify Installation

Test your setup by running the help command:
```bash
python coubyuinst.py --help
```

If everything is installed correctly, you should see the help documentation with all available commands and options.

## Usage Examples

### Basic YouTube Operations

**Download a Single Video (MP4 format):**
```bash
python snapstream.py youtube-video --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format mp4
```
This downloads the specified video in MP4 format to the `youtube_videos` folder, maintaining original quality up to 1080p resolution.

**Extract Audio Only (MP3 format):**
```bash
python snapstream.py youtube-video --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --format mp3
```
This extracts only the audio track and converts it to MP3 format at 192 kbps quality.

**Download Complete Playlist:**
```bash
python snapstream.py youtube-playlist --url "https://www.youtube.com/playlist?list=PLxxxxxxxxxxx" --format mp4
```
Downloads all videos in the playlist, creating a subfolder named after the playlist title.

### Instagram Content Management

**Single Post Download:**
```bash
python snapstream.py instagram-download --url "https://www.instagram.com/p/ABC123XYZ/"
```
Downloads the specified Instagram post, handling both single images/videos and carousel posts automatically.

**Batch Processing from File:**

First, create a text file (`instagram_urls.txt`) with URLs:
```
https://www.instagram.com/p/ABC123XYZ/
https://www.instagram.com/p/DEF456UVW/
https://www.instagram.com/reel/GHI789RST/
```

Then run the batch download:
```bash
python snapstream.py instagram-download --file instagram_urls.txt --format mp4 --out my_downloads
```

**Audio Extraction from Instagram Videos:**
```bash
python snapstream.py instagram-download --url "https://www.instagram.com/reel/ABC123XYZ/" --format mp3
```

### Coub Content Archiving

**Download Liked Videos:**
```bash
python coubyuinst.py coub-likes --session "_coub_session=your_session_here" --token "remember_token=your_token_here"
```

### Coub Authentication Process

**Session Cookie Extraction:**

1. **Log into Coub.com** using your browser
2. **Open Developer Tools** (F12)
3. **Go to Application → Cookies → https://coub.com**
4. **Find and copy these values:**
   - `_coub_session`: Your session cookie
   - `remember_token`: Your remember token

**Important Security Notes:**
- Never share your session cookies with others
- Cookies expire periodically and need to be refreshed
- Always log out of shared computers to protect your authentication data

### Error Log Analysis

The script creates error logs (`error_log_01.txt`) for failed downloads. Common error patterns include:

- **Network timeouts**: Usually resolved by retrying the download
- **Format not available**: The requested format may not exist for that content
- **Authentication required**: Private content requires proper authentication setup

## File Structure

After running the script, your directory structure will look like this:

```
your-project-directory/
├── coubyuinst.py                 # Main script file
├── hata_log_01.txt              # Error log (created automatically)
├── youtube_videos/              # YouTube downloads
│   ├── video_title.mp4
│   ├── video_title.mp3
│   └── Playlist Name/           # Playlist subfolder
│       ├── video1.mp4
│       └── video2.mp4
├── instagram_videos/            # Instagram downloads (default)
│   ├── 01-post_id-title.mp4
│   ├── 01-1-carousel_item.jpg
│   └── 01-2-carousel_item.mp4
├── coub_likes/                  # Coub downloads
│   ├── coub_video1.mp4
│   └── coub_video2.mp4
└── custom_folder/               # Custom output folder
    └── downloaded_content.mp4
```

### File Naming Conventions

**YouTube Files:**
- Single videos: `{original_title}.mp4`
- Playlist videos: `{playlist_name}/{video_title}.mp4`

**Instagram Files:**
- Single posts: `{index}-{post_id}-{title}.mp4`
- Carousel items: `{index}-{item_number}-{post_id}-{title}.mp4`

**Coub Files:**
- `{title}.mp4` or `coub_{id}.mp4` if title is unavailable

## Legal Considerations

### Usage Responsibility

**Content Ownership:** Always ensure you have the right to download and use the content. This tool should only be used for:
- Content you own or have created
- Content with explicit permission from the copyright holder
- Content under Creative Commons or similar permissive licenses
- Fair use educational or research purposes (jurisdiction-dependent)

**Platform Terms of Service:** Be aware that downloading content may violate platform terms of service. Review each platform's terms before using this tool:
- YouTube Terms of Service
- Instagram Terms of Use  
- Coub Terms and Conditions

**Rate Limiting and Respectful Usage:** The script includes built-in delays to respect platform resources. Avoid:
- Excessive concurrent downloads
- Downloading copyrighted content without permission
- Circumventing platform access controls

### Privacy Considerations

**Authentication Data Security:**
- Never share your session cookies or authentication tokens
- Store authentication data securely and delete when no longer needed
- Be aware that using authentication data on shared computers poses security risks

**Content Privacy:** Respect the privacy settings of content creators. Don't download or redistribute private content without explicit permission.

---

## Support and Contributing

If you encounter issues or have suggestions for improvements, please ensure you have:
1. Followed all installation steps correctly
2. Verified your Python and FFmpeg installations
3. Checked the error logs for specific error messages
4. Tested with different URLs to isolate the problem

you want me to continue developing this project, then just leave a star.