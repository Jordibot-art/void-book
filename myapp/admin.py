from django.contrib import admin
from .models import Novel, Chapter

# This customizes how Novels look in the admin panel
class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'rating', 'badge', 'is_featured', 'created_at')
    search_fields = ('title', 'genre')
    list_filter = ('genre', 'badge', 'is_featured')
    list_editable = ('is_featured',)  # Allow quick toggle of featured status
    ordering = ('-created_at',)  # Show newest first

# This customizes how Chapters look
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('novel', 'chapter_number', 'created_at')
    search_fields = ('novel__title',)
    list_filter = ('novel',)
    ordering = ('-created_at',)  # Show newest first

# Register them to the dashboard
admin.site.register(Novel, NovelAdmin)
admin.site.register(Chapter, ChapterAdmin)
