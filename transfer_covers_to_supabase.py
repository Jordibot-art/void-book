import os
import mimetypes
import urllib.request
import urllib.error
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent

# Supabase config
SUPABASE_URL = "https://zenknnjfexumefmsabgu.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InplbmtubmpmZXh1bWVmbXNhYmd1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk4ODA5MiwiZXhwIjoyMTA3NTY0MDkyfQ.JWyz4hAT_tlw851P0sA2vpuXqeFdGmAFcH4hgAHMAmQ"
BUCKET = "covers"

def upload_file(local_path, remote_path):
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{remote_path}"
    content_type, _ = mimetypes.guess_type(str(local_path))
    content_type = content_type or "image/jpeg"
    
    with open(local_path, "rb") as f:
        data = f.read()
        
    headers = {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "apikey": SERVICE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f" [OK] Uploaded -> {remote_path} ({len(data):,} bytes)")
            return True
    except urllib.error.HTTPError as e:
        # Retry with PUT if conflict
        put_req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
        try:
            with urllib.request.urlopen(put_req) as resp:
                print(f" [OK (PUT)] Uploaded -> {remote_path} ({len(data):,} bytes)")
                return True
        except Exception as put_err:
            print(f" [ERROR] Failed to upload {remote_path}: {e.code} / {put_err}")
            return False
    except Exception as e:
        print(f" [ERROR] Failed to upload {remote_path}: {e}")
        return False

def verify_public_url(remote_path):
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{remote_path}"
    try:
        with urllib.request.urlopen(public_url) as resp:
            if resp.status == 200:
                return True
    except Exception as e:
        return False
    return False

def main():
    print("=" * 60)
    print("Transferring VoidBook cover images to Supabase Storage Bucket...")
    print(f"Target Bucket: {BUCKET}")
    print("=" * 60)
    
    files_to_transfer = {}

    # 1. Media covers (used by existing novels)
    media_covers_dir = BASE_DIR / "media" / "covers"
    if media_covers_dir.exists():
        for f in media_covers_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                # Upload as both 'covers/<name>' (which matches Django's novel.cover_image)
                files_to_transfer[f"covers/{f.name}"] = f
                # And flat '<name>'
                files_to_transfer[f"{f.name}"] = f

    # 2. Project root covers directory
    root_covers_dir = BASE_DIR / "covers"
    if root_covers_dir.exists():
        for f in root_covers_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                files_to_transfer[f"covers/{f.name}"] = f
                files_to_transfer[f"{f.name}"] = f

    # 3. Static covers if any
    static_images_dir = BASE_DIR / "myapp" / "static" / "myapp" / "images"
    if static_images_dir.exists():
        for f in static_images_dir.iterdir():
            if f.is_file() and f.suffix.lower() in [".jpg", ".png", ".webp", ".jpeg"]:
                files_to_transfer[f"covers/{f.name}"] = f
                files_to_transfer[f"{f.name}"] = f

    print(f"Found {len(files_to_transfer)} unique destination paths to sync.\n")
    
    success_count = 0
    for remote_path, local_path in files_to_transfer.items():
        if upload_file(local_path, remote_path):
            success_count += 1
            
    print("\n" + "=" * 60)
    print(f"Upload Complete: {success_count}/{len(files_to_transfer)} uploaded successfully.")
    print("=" * 60)

    print("\nVerifying public accessibility for live novels in Supabase database...")
    import django
    os.environ["DJANGO_SETTINGS_MODULE"] = "myproject.settings"
    django.setup()
    from myapp.models import Novel

    novels = Novel.objects.all()
    verified = 0
    for novel in novels:
        if novel.cover_image:
            url = novel.cover_image.url
            clean_remote = str(novel.cover_image.name).replace('\\', '/').lstrip('/')
            ok = verify_public_url(clean_remote)
            status_symbol = "[OK]" if ok else "[FAIL]"
            print(f" {status_symbol} [{novel.id}] {novel.title[:35]:<35} -> {url}")
            if ok:
                verified += 1
                
    print(f"\nVerification: {verified}/{len(novels)} novels have verified public CDN cover URLs in Supabase!")

if __name__ == "__main__":
    main()
