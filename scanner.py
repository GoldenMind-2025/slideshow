import os
import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

class PhotoScanner:
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heif', '.bmp', '.gif', '.mp4', '.mov', '.m4v'}
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.m4v'}

    def __init__(self, directory):
        # Resolve tilde (~) and relative paths to absolute paths
        self.directory = Path(directory).expanduser().resolve()
        self.photos = []
        
        if not self.directory.exists():
            print(f"WARNING: Directory does not exist: {self.directory}")
        elif not self.directory.is_dir():
            print(f"WARNING: Path is not a directory: {self.directory}")

    def scan(self):
        """Recursively scan the directory for photos and group by album."""
        grouped_photos = {} # {album_name: [photo_metadata, ...]}
        for root, _, files in os.walk(self.directory):
            for file in files:
                if Path(file).suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    full_path = Path(root) / file
                    metadata = self._get_photo_metadata(full_path)
                    album = metadata['album']
                    if album not in grouped_photos:
                        grouped_photos[album] = []
                    grouped_photos[album].append(metadata)
        
        # Sort photos within each album by date/path
        for album in grouped_photos:
            grouped_photos[album].sort(key=lambda x: (x['date_taken'], x['path']))
            
        return grouped_photos

    def _get_photo_metadata(self, path):
        """Extract metadata for a single photo."""
        # Use the relative path from the scan root as the album name
        # This preserves hierarchy like 'Travel/Trip1'
        try:
            rel_path = path.parent.relative_to(self.directory)
            if str(rel_path) == '.':
                album = "Root"
            else:
                album = str(rel_path)
        except ValueError:
            album = path.parent.name
        
        ext = path.suffix.lower()
        is_video = ext in self.VIDEO_EXTENSIONS
        
        metadata = {
            'path': str(path),
            'filename': path.name,
            'album': path.parent.name,
            'date_taken': "Unknown",
            'type': 'video' if is_video else 'photo'
        }
        
        if is_video:
            # For videos, use modification time as default
            try:
                mod_time = os.path.getmtime(path)
                metadata['date_taken'] = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            except: pass
            return metadata

        # Existing photo EXIF logic...
        try:
            metadata['date_taken'] = self._get_date_taken(path)
        except Exception:
            metadata['date_taken'] = self._get_file_mtime(path) # Fallback for photos if EXIF fails
        return metadata

    def _get_date_taken(self, path):
        """Extract date taken from EXIF data."""
        try:
            with Image.open(path) as img:
                exif = img.getexif()
                if not exif:
                    return self._get_file_mtime(path)
                
                # Search for DateOriginal (36867) or DateTime (306)
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ('DateTimeOriginal', 'DateTime'):
                        return value[:10].replace(':', '-') # YYYY-MM-DD
        except Exception:
            pass
        return self._get_file_mtime(path)

    def _get_file_mtime(self, path):
        """Fallback to file modification time."""
        try:
            mtime = os.path.getmtime(path)
            from datetime import datetime
            return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
        except Exception:
            return "No Date"

    def scan_music(self, music_directory):
        """Recursively scan for music files."""
        music_dir = Path(music_directory).expanduser().resolve()
        music_files = []
        supported_audio = {'.mp3', '.ogg', '.wav'}
        
        if not music_dir.exists():
            return []

        for root, _, files in os.walk(music_dir):
            for file in files:
                if Path(file).suffix.lower() in supported_audio:
                    music_files.append(str(Path(root) / file))
        
        return music_files
