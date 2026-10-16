import os
import re
import ast
from django.core.management.base import BaseCommand
from myapp.models import Novel, Chapter
from django.conf import settings

class Command(BaseCommand):
    help = 'Imports novels from data.js into the database'

    def handle(self, *args, **kwargs):
        # Path to data.js
        file_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'myapp', 'data.js')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find the array content between "let mangas =" and the closing ";"
        match = re.search(r'let mangas = (\[.*?\]);', content, re.DOTALL)
        if not match:
            self.stdout.write(self.style.ERROR('Could not find "let mangas = [...]" in data.js'))
            return

        js_content = match.group(1)

        # Clean up JS to make it Python-friendly for evaluation
        # 1. Remove single line comments //...
        js_content = re.sub(r'//.*', '', js_content)
        # 2. Quote unquoted keys (e.g., id: -> "id":)
        # Matches a key followed by colon, preceded by {, comma, or start of line
        js_content = re.sub(r'([,{]\s*)([a-zA-Z0-9_]+):', r'\1"\2":', js_content)
        # 3. Replace JS backticks with Python triple quotes for multi-line strings
        js_content = js_content.replace('`', '"""')
        # 4. Replace JS null with Python None
        js_content = js_content.replace('null', 'None')

        try:
            # Evaluate the cleaned string as a Python list
            mangas = eval(js_content)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to parse data: {e}'))
            return

        self.stdout.write(f'Found {len(mangas)} novels to import...')

        for m in mangas:
            # Create or Update Novel
            novel, created = Novel.objects.get_or_create(
                title=m.get('title'),
                defaults={
                    'genre': m.get('genre', 'Unknown'),
                    'rating': m.get('rating', 0),
                    'badge': m.get('badge'),
                    'color': m.get('color', ''),
                    'kanji': m.get('kanji', ''),
                }
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(f'{action} Novel: {novel.title}')

            # Create Chapters
            chapters = m.get('chapters', {})
            for ch_num, content in chapters.items():
                # content in data.js is a list of paragraphs. Join them for the TextField.
                if isinstance(content, list):
                    body = "\n\n".join(content)
                else:
                    body = str(content)
                
                Chapter.objects.get_or_create(
                    novel=novel,
                    chapter_number=ch_num,
                    defaults={'content': body}
                )

        self.stdout.write(self.style.SUCCESS('Successfully imported novels and chapters!'))