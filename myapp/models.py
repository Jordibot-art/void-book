from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone

# 1. USER LIBRARY MODEL (Handles Bookmarks & History)
class UserLibrary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    bookmarks = models.JSONField(default=list, blank=True)
    read_history = models.JSONField(default=list, blank=True)
    progress = models.JSONField(default=dict, blank=True)
    saved_words = models.JSONField(default=dict, blank=True) 

    def __str__(self):
        return f"{self.user.username}'s Library"


# 2. NOVEL MODEL (Handles the Book Details in Admin)
class Novel(models.Model):
    HERO_SLOT_CHOICES = [
        (1, 'Hero Slot 1'),
        (2, 'Hero Slot 2'),
        (3, 'Hero Slot 3'),
    ]

    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=50)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    badge = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 'hot', 'new'")
    color = models.CharField(max_length=100, default="linear-gradient(135deg,#1a0533,#3d0a6b,#ff3c5f)")
    kanji = models.CharField(max_length=10)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields for dynamic index management
    is_featured = models.BooleanField(default=False, help_text="Show this novel in the Featured 2 Novels section")
    position = models.CharField(max_length=20, blank=True, default="center", help_text="Image position (e.g., '20% 50%')")
    hero_slot = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=HERO_SLOT_CHOICES,
        help_text="Select a homepage hero slot for this novel.",
    )
    
    def __str__(self):
        return self.title

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hero_slot'],
                condition=Q(hero_slot__isnull=False),
                name='unique_hero_slot_when_set',
            )
        ]


# 3. CHAPTER MODEL (Handles the Story Text in Admin)
class Chapter(models.Model):
    novel = models.ForeignKey(Novel, related_name='chapters', on_delete=models.CASCADE)
    chapter_number = models.IntegerField()
    content = models.TextField(help_text="Paste the chapter text here. Use double enters for paragraphs.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chapter_number'] # Always order chapters from lowest to highest

    def __str__(self):
        return f"{self.novel.title} - Chapter {self.chapter_number}"


# 4. ACTIVITY LOG MODEL (Tracks all admin actions)
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('novel_created', 'Novel Created'),
        ('novel_updated', 'Novel Updated'),
        ('novel_deleted', 'Novel Deleted'),
        ('novel_featured', 'Novel Featured'),
        ('novel_unfeatured', 'Novel Unfeatured'),
        ('chapter_created', 'Chapter Created'),
        ('chapter_deleted', 'Chapter Deleted'),
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_banned', 'User Banned'),
        ('user_unbanned', 'User Unbanned'),
        ('system', 'System'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    actor = models.CharField(max_length=100, blank=True, help_text="Username of who performed the action")
    novel_title = models.CharField(max_length=200, blank=True, help_text="Related novel title if applicable")
    novel_id = models.IntegerField(blank=True, null=True, help_text="Related novel ID if applicable")
    chapter_number = models.IntegerField(blank=True, null=True, help_text="Related chapter number if applicable")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_activity(cls, action, description, actor='', novel_title='', novel_id=None, chapter_number=None):
        """Helper method to create activity log entries"""
        return cls.objects.create(
            action=action,
            description=description,
            actor=actor,
            novel_title=novel_title,
            novel_id=novel_id,
            chapter_number=chapter_number
        )
    
    @classmethod
    def get_recent_activities(cls, limit=20):
        """Get recent activities for the dashboard"""
        return cls.objects.all()[:limit]
