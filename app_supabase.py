import streamlit as st
import time
import io
import base64
import random
from datetime import datetime
from PIL import Image, ImageOps
from supabase import create_client, Client

st.set_page_config(page_title="Photo Slideshow", layout="centered", page_icon="📸")

# Connect to Supabase
if "SUPABASE_URL" not in st.secrets or "SUPABASE_KEY" not in st.secrets:
    st.error("Missing Supabase credentials in Streamlit secrets!")
    st.stop()

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# You can change this to match your Supabase bucket name
BUCKET_NAME = "slideshow-media" 

@st.cache_data(ttl=3600)
def scan_supabase_bucket():
    """Recursively scans the Supabase bucket for media and overlay files."""
    def get_all_files(folder_path=""):
        all_files = []
        try:
            items = supabase.storage.from_(BUCKET_NAME).list(folder_path)
            for item in items:
                name = item['name']
                if name == '.emptyFolderPlaceholder': continue
                current_path = f"{folder_path}/{name}" if folder_path else name
                
                # Use the presence of a file extension to identify files
                # This guarantees overlay.txt is recognized even if Supabase drops its metadata
                if '.' in name:
                    all_files.append(current_path)
                else:
                    all_files.extend(get_all_files(current_path))
        except Exception as e:
            print(f"Error scanning {folder_path}: {e}")
        return all_files
        
    files = get_all_files()
    
    # Filter files
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.heif')
    photos = [f for f in files if f.lower().endswith(valid_exts) and 'slideshow_photos' in f]
    music = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.ogg')) and 'slideshow_music' in f]
    overlays = [f for f in files if f.lower().endswith('overlay.txt')]
    
    # Pre-download and parse overlay files into a dictionary cache
    overlay_cache = {}
    for ov in overlays:
        try:
            data = supabase.storage.from_(BUCKET_NAME).download(ov)
            text = data.decode('utf-8', errors='ignore')
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            album_override = lines[0][:20] if len(lines) > 0 else None
            date_override = None
            
            if len(lines) > 1:
                d = lines[1].strip('"\'')
                for fmt in ["%d-%b-%Y", "%d-%B-%Y", "%d-%b-%y", "%d-%B-%y", "%d-%m-%Y"]:
                    try:
                        datetime.strptime(d, fmt)
                        date_override = d
                        break
                    except ValueError:
                        pass
                        
            parent = ov.rsplit('/', 1)[0] if '/' in ov else ""
            overlay_cache[parent] = (album_override, date_override)
            print(f"Successfully loaded overlay for {parent}: Album='{album_override}', Date='{date_override}'")
        except Exception as e:
            print(f"Failed to parse overlay {ov}: {e}")
            
    return photos, music, overlay_cache

def extract_exif_date(img):
    try:
        exif = img.getexif()
        if exif:
            for tag_id, value in exif.items():
                if tag_id in (36867, 306): # DateTimeOriginal or DateTime
                    return value[:10].replace(':', '-')
    except:
        pass
    return "Unknown"

def main():
    st.markdown("<h1 style='text-align: center;'>📸 Mothiaai Photo Slideshow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Powered by Supabase Cloud Storage</p>", unsafe_allow_html=True)

    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
        
    with st.spinner("Scanning Cloud Storage..."):
        photos, music_tracks, overlay_cache = scan_supabase_bucket()
        
    if not photos:
        st.error(f"No photos found in the '{BUCKET_NAME}' bucket.")
        return
        
    # UI Controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.get('finished', False) and not st.session_state.is_playing:
            st.info("End of Slideshow")
            
        if not st.session_state.is_playing:
            if st.button("▶️ Start Slideshow", width='stretch'):
                st.session_state.is_playing = True
                st.session_state.finished = False
                st.rerun()
        else:
            if st.button("⏹ Stop Slideshow", width='stretch'):
                st.session_state.is_playing = False
                st.rerun()
                
    # Slideshow Loop
    if st.session_state.is_playing:
        st.markdown("---")
        
        # Audio injection
        if music_tracks:
            track_path = random.choice(music_tracks)
            try:
                audio_bytes = supabase.storage.from_(BUCKET_NAME).download(track_path)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                audio_html = f"""
                    <audio autoplay loop style="display:none;">
                        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            except Exception as e:
                print(f"Audio error: {e}")
            
        image_container = st.empty()
        text_container = st.empty()
        progress_container = st.empty()
        
        total = len(photos)
        
        for idx, photo_path in enumerate(photos):
            try:
                # 1. Download image from cloud
                img_bytes = supabase.storage.from_(BUCKET_NAME).download(photo_path)
                
                # 2. Process image with PIL
                with Image.open(io.BytesIO(img_bytes)) as img:
                    img = ImageOps.exif_transpose(img)
                    date_taken = extract_exif_date(img)
                    
                    # Shrink high-res photos to prevent memory crashes
                    img.thumbnail((1920, 850), Image.Resampling.LANCZOS)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=85)
                    img_b64 = base64.b64encode(buffer.getvalue()).decode()
                    
                # 3. Retrieve Metadata
                parent = photo_path.rsplit('/', 1)[0]
                default_album = parent.split('/')[-1] if '/' in parent else parent
                ov_album, ov_date = overlay_cache.get(parent, (None, None))
                
                final_album = ov_album if ov_album else default_album
                final_date = ov_date if ov_date else date_taken
                final_album = "Mothiaai Birthday"
                final_date = "26-Apr-26"

                # 4. Render to Screen
                html = f"""
                    <div style="display: flex; justify-content: center; align-items: center; width: 100%; max-height: 75vh;">
                        <img src="data:image/jpeg;base64,{img_b64}" style="max-width: 100%; max-height: 75vh; object-fit: contain; border-radius: 4px;">
                    </div>
                """
                image_container.markdown(html, unsafe_allow_html=True)
                text_container.markdown(f"<h3 style='text-align: center; color: #a9a9a9;'>{final_album} &nbsp; | &nbsp; {final_date}</h3>", unsafe_allow_html=True)
                progress_container.progress((idx + 1) / total)
                
            except Exception as e:
                print(f"Error processing {photo_path}: {e}")
                
            time.sleep(5)
            
        # End of slideshow
        st.session_state.is_playing = False
        st.session_state.finished = True
        st.rerun()

if __name__ == "__main__":
    main()
