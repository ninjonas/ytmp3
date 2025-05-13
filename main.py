import os
import yt_dlp
from pathlib import Path
from yt_dlp.utils import sanitize_filename
from tqdm import tqdm
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM, APIC
import requests
import io

def set_mp3_metadata(file_path, metadata):
    """
    Sets metadata tags on an MP3 file using mutagen
    
    Parameters:
    - file_path: Path to the MP3 file
    - metadata: Dictionary containing metadata keys:
      - title: Song title
      - artist: Artist name
      - album: Album name
      - year: Release year
      - genre: Music genre
      - comment: Additional comments
      - thumbnail_url: URL to album art image
    """
    try:
        # Create ID3 tag object - create it if doesn't exist
        try:
            tags = ID3(file_path)
        except:
            tags = ID3()
        
        # Set the tags based on provided metadata
        if 'title' in metadata and metadata['title']:
            tags['TIT2'] = TIT2(encoding=3, text=metadata['title'])
        
        if 'artist' in metadata and metadata['artist']:
            tags['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
        
        if 'album' in metadata and metadata['album']:
            tags['TALB'] = TALB(encoding=3, text=metadata['album'])
            
        if 'year' in metadata and metadata['year']:
            tags['TDRC'] = TDRC(encoding=3, text=str(metadata['year']))
            
        if 'genre' in metadata and metadata['genre']:
            tags['TCON'] = TCON(encoding=3, text=metadata['genre'])
            
        if 'comment' in metadata and metadata['comment']:
            tags['COMM'] = COMM(encoding=3, lang='eng', desc='', text=metadata['comment'])
            
        # Add album art if URL is provided
        if 'thumbnail_url' in metadata and metadata['thumbnail_url']:
            try:
                response = requests.get(metadata['thumbnail_url'])
                if response.status_code == 200:
                    image_data = response.content
                    tags['APIC'] = APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,  # Cover image
                        desc='Cover',
                        data=image_data
                    )
            except Exception as e:
                print(f"Failed to add album art: {e}")
        
        # Save the tags to the file
        tags.save(file_path)
        print(f"Metadata added to: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"Error setting metadata for {file_path}: {str(e)}")
        return False

def download_youtube_audio(url, output_path='./downloaded-mp3'):
    """
    Downloads YouTube audio and converts to MP3
    Only adds artist name when not already in title
    Also adds metadata to the MP3 file
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    # Custom progress bar hook
    def my_hook(d):
        if d['status'] == 'downloading':
            if 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                # Calculate percentage based on downloaded bytes and total estimated bytes
                percentage = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                # Update progress bar to the calculated percentage
                progress.update(percentage - progress.n)
                
            if '_speed_str' in d:
                progress.set_postfix({"Speed": d['_speed_str']})
                
        elif d['status'] == 'finished':
            # When download finishes, ensure bar is at 100%
            progress.update(100 - progress.n)

    # First extract info without downloading
    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # Extract all available metadata
        artist = info.get('uploader', '') or info.get('artist', '')
        title = info.get('title', '')
        album = info.get('album', '') or info.get('playlist_title', '') or 'YouTube Music'
        release_year = info.get('release_year', '') or info.get('upload_date', '')[:4] if info.get('upload_date', '') else ''
        genre = info.get('genre', '') or info.get('categories', ['Music'])[0] if info.get('categories') else 'Music'
        description = info.get('description', '')
        thumbnail_url = info.get('thumbnail', '') if isinstance(info.get('thumbnail', ''), str) else info.get('thumbnails', [{}])[0].get('url', '')
        
        # Prepare metadata dictionary
        metadata = {
            'title': title,
            'artist': artist,
            'album': album,
            'year': release_year,
            'genre': genre,
            'comment': description[:250] if description else '',  # Truncate long descriptions
            'thumbnail_url': thumbnail_url
        }
        
        # Clean and compare names
        clean_artist = artist.lower().replace(" ", "")
        clean_title = title.lower().replace(" ", "")
        
        # Check if artist name appears in title (fuzzy match)
        artist_in_title = (
            clean_artist in clean_title or 
            any(part in clean_title for part in clean_artist.split())
        )

        # Handle common title patterns
        if " - " in title and not artist_in_title:
            base = f"{artist} - {title}"
        elif artist_in_title:
            base = title
        else:
            base = f"{artist} - {title}"

        # Sanitize filename and replace underscores with hyphens
        sanitized_base = sanitize_filename(base, restricted=True)
        sanitized_base = sanitized_base.replace('_', ' ')
        final_filename = f"{sanitized_base}.mp3"
        outtmpl = os.path.join(output_path, f"{sanitized_base}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [my_hook],
        # Request additional metadata
        'writethumbnail': False,  # We'll handle thumbnail separately
        'writeinfojson': False,   # We don't need the info JSON
    }

    try:
        # Initialize progress bar
        print(f"Downloading: {title}")
        with tqdm(total=100, unit='%', desc="Downloading", ncols=80) as progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
        # Full path to the downloaded file
        mp3_path = os.path.join(output_path, final_filename)
        
        # Set metadata tags on the MP3 file
        print("Adding metadata to MP3 file...")
        set_mp3_metadata(mp3_path, metadata)
            
        print(f"Success: {final_filename}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def download_youtube_playlist(playlist_url, output_path='./downloaded-mp3'):
    """
    Downloads all videos from a YouTube playlist and converts them to MP3
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Configure yt-dlp to extract playlist info
    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,  # Skip entries that have errors
        'extract_flat': 'in_playlist',  # Better handling of playlists
        'no_warnings': True,
    }

    # First, extract all video URLs from the playlist
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            if not playlist_info or 'entries' not in playlist_info or not playlist_info['entries']:
                print(f"Error: Could not find videos in the playlist {playlist_url}")
                return False
                
            total_videos = len(playlist_info['entries'])
            playlist_title = playlist_info.get('title', 'YouTube Playlist')
            print(f"Found {total_videos} videos in playlist: {playlist_title}")
            
            # Create a subfolder for the playlist with a sanitized name
            playlist_folder = sanitize_filename(playlist_title, restricted=True)
            playlist_folder = playlist_folder.replace('_', ' ')
            playlist_path = os.path.join(output_path, playlist_folder)
            Path(playlist_path).mkdir(exist_ok=True)
            
            # Download each video in the playlist with a progress bar
            successful = 0
            with tqdm(total=total_videos, unit='videos', desc="Playlist progress", position=0, leave=True) as pbar:
                for i, entry in enumerate(playlist_info['entries'], 1):
                    if entry is None:
                        continue
                    
                    # Handle different entry formats based on extraction method
                    if 'url' in entry:
                        video_url = entry['url']
                        if not video_url.startswith('http'):
                            video_url = f"https://www.youtube.com/watch?v={video_url}"
                    elif 'id' in entry:
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    else:
                        print(f"Skipping entry {i}: Could not extract video URL")
                        pbar.update(1)
                        continue
                        
                    title = entry.get('title', 'Untitled')
                    print(f"\n[{i}/{total_videos}] Processing: {title}")
                    
                    if download_youtube_audio(video_url, playlist_path):
                        successful += 1
                    
                    pbar.update(1)
                    
            print(f"\nPlaylist download complete: {successful}/{total_videos} videos were successfully downloaded to '{playlist_path}'")
            return successful > 0
            
        except Exception as e:
            print(f"Error processing playlist {playlist_url}: {str(e)}")
            return False

def is_playlist(url):
    """
    Check if the URL is a playlist by looking for common playlist identifiers
    """
    return 'playlist' in url.lower() or '&list=' in url or '?list=' in url

def add_metadata_to_existing_files(directory):
    """
    Process existing MP3 files in a directory to add/update metadata
    based on their filenames
    """
    print(f"Processing existing MP3 files in: {directory}")
    processed = 0
    failed = 0
    
    for root, _, files in os.walk(directory):
        mp3_files = [f for f in files if f.lower().endswith('.mp3')]
        if not mp3_files:
            continue
            
        print(f"Found {len(mp3_files)} MP3 files in {root}")
        
        for mp3_file in mp3_files:
            try:
                file_path = os.path.join(root, mp3_file)
                print(f"Processing: {mp3_file}")
                
                # Extract artist and title from filename
                filename_without_ext = os.path.splitext(mp3_file)[0]
                
                # Try to split by " - " first
                parts = filename_without_ext.split(" - ", 1)
                
                if len(parts) > 1:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    # If no separator, use the filename as title and folder name as artist
                    title = filename_without_ext.strip()
                    artist = os.path.basename(root)
                
                # Get album from parent folder name
                album = os.path.basename(root)
                
                # Create metadata dictionary
                metadata = {
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'genre': 'Music',  # Default genre
                }
                
                # Set the metadata
                if set_mp3_metadata(file_path, metadata):
                    processed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"Error processing {mp3_file}: {str(e)}")
                failed += 1
                
    print(f"Metadata processing complete: {processed} successful, {failed} failed")
    return processed > 0

if __name__ == "__main__":
    print("YouTube to MP3 Downloader and Metadata Editor")
    
    url = input("Enter YouTube URL: ")

    # Check if it's a playlist URL before using yt-dlp
    if is_playlist(url):
        print("Detected playlist URL. Starting playlist download...")
        download_youtube_playlist(url)
    else:
        # If not clearly a playlist from URL pattern, let's try to check with yt-dlp
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False, process=False)
                
                # Check if it's a playlist
                if info.get('_type') == 'playlist':
                    print("Detected playlist URL. Starting playlist download...")
                    download_youtube_playlist(url)
                else:
                    print("Detected single video URL. Starting download...")
                    download_youtube_audio(url)
            except Exception as e:
                print(f"Error processing URL: {str(e)}")