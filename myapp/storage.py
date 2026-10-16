import os
import json
import mimetypes
import urllib.request
import urllib.error
from io import BytesIO
from django.core.files.base import File
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    """
    Custom Django Storage backend that uploads media files directly to
    a Supabase Storage bucket using Supabase REST API (zero heavy dependencies).
    """

    def __init__(self, bucket_name=None, supabase_url=None, service_key=None):
        self.bucket_name = bucket_name or getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'covers')
        self.supabase_url = (supabase_url or getattr(settings, 'SUPABASE_URL', '')).rstrip('/')
        self.service_key = service_key or getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '')

    def _get_headers(self, content_type=None):
        headers = {
            'Authorization': f'Bearer {self.service_key}',
            'apikey': self.service_key,
        }
        if content_type:
            headers['Content-Type'] = content_type
        return headers

    def _normalize_name(self, name):
        clean = str(name).replace('\\', '/').lstrip('/')
        return clean

    def _save(self, name, content):
        clean_name = self._normalize_name(name)
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{clean_name}"

        content_type, _ = mimetypes.guess_type(clean_name)
        content_type = content_type or 'application/octet-stream'

        headers = self._get_headers(content_type)
        headers['x-upsert'] = 'true'

        if hasattr(content, 'chunks'):
            data = b''.join(chunk for chunk in content.chunks())
        else:
            data = content.read()

        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as resp:
                pass
        except urllib.error.HTTPError as e:
            # If POST fails with duplicate or conflict, try PUT with upsert
            put_req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
            try:
                with urllib.request.urlopen(put_req) as resp:
                    pass
            except Exception as put_err:
                raise IOError(f"Failed to upload {clean_name} to Supabase Storage: {e.code} {e.reason} / {put_err}")

        return clean_name

    def _open(self, name, mode='rb'):
        clean_name = self._normalize_name(name)
        url = self.url(clean_name)
        try:
            with urllib.request.urlopen(url) as resp:
                return File(BytesIO(resp.read()), name=clean_name)
        except Exception as e:
            raise IOError(f"Failed to download {clean_name} from Supabase: {e}")

    def exists(self, name):
        # Allow upserting without Django generating random duplicate suffix strings
        return False

    def delete(self, name):
        clean_name = self._normalize_name(name)
        url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}"
        data = json.dumps({'prefixes': [clean_name]}).encode('utf-8')
        headers = self._get_headers('application/json')
        req = urllib.request.Request(url, data=data, headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(req) as resp:
                pass
        except Exception:
            pass

    def url(self, name):
        clean_name = self._normalize_name(name)
        if clean_name.startswith('http://') or clean_name.startswith('https://'):
            return clean_name
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{clean_name}"
