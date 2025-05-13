# YouTube to MP3 Downloader and Metadata Editor

A Python tool to download YouTube videos/playlists as MP3 files with proper metadata.

## Features

- Download single YouTube videos as MP3 files
- Download entire YouTube playlists as MP3s, organized in folders
- Automatically extract and add metadata (artist, title, album, etc.)
- Add album art thumbnails from YouTube
- Smart naming convention that properly formats artist and title
- Process existing MP3 files to add/update metadata

## Requirements

- Python 3.6 or higher
- FFmpeg (for audio conversion)

## Installation

1. Clone this repository or download the source code
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Make sure FFmpeg is installed on your system:
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `apt-get install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

## Usage

### Basic Usage

Run the script and follow the prompts:

```bash
python main.py
```

When prompted, enter a YouTube URL. The script will automatically detect if it's a single video or a playlist.

### YouTube Video URLs

The script supports various YouTube URL formats:

- Single video: `https://www.youtube.com/watch?v=VIDEO_ID`
- Playlist: `https://www.youtube.com/playlist?list=PLAYLIST_ID` 
- Mixed format (will be detected as playlist): `https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID`

### Output

- Single videos are saved to the `./downloaded-mp3/` directory
- Playlist videos are saved to a subfolder named after the playlist
- MP3 files are named using the pattern: `Artist - Title.mp3`
- Metadata (ID3 tags) is automatically added to each file

### Adding Metadata to Existing Files

To process existing MP3 files and add metadata based on their filenames:

1. Modify the `main.py` file and call the `add_metadata_to_existing_files(directory)` function with the path to your MP3 files
2. Run the script

## How It Works

1. The script uses yt-dlp to extract video information and download audio
2. FFmpeg is used to convert the audio to MP3 format
3. Mutagen is used to add ID3 tags (metadata) to the MP3 files
4. For playlists, files are organized in a subfolder named after the playlist

## Example

```
YouTube to MP3 Downloader and Metadata Editor
Enter YouTube URL: https://www.youtube.com/watch?v=c0D2h71bFFI&list=PLvourwKkGIh8spXQ0ZrjGLzLS2kMMnL6T
Detected playlist URL. Starting playlist download...
Found 12 videos in playlist: Afro House
[1/12] Processing: Teke Teke
Downloading: Teke Teke
...
```

## Troubleshooting

- If you encounter errors about missing FFmpeg, ensure it's properly installed and available in your system PATH
- For issues with specific YouTube videos, try using a different video URL
- Make sure you have a stable internet connection for downloading videos

## License

This project is open-source and available for personal use. Please respect YouTube's terms of service when using this tool.

## Disclaimer

This tool is intended for downloading content that you have the right to download. Please respect copyright laws and YouTube's Terms of Service.