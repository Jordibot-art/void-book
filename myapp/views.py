import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import UserLibrary, Novel, Chapter, ActivityLog
from django.contrib.admin.views.decorators import staff_member_required

# 1. MAIN PAGE RENDER
@ensure_csrf_cookie
def home(request):
    return render(request, 'myapp/index.html')

# 1.5 CUSTOM ADMIN DASHBOARD
def custom_admin(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return render(request, 'myapp/index.html')
    return render(request, 'myapp/custom_admin.html')

# 2. REGISTER API
def api_register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        library = UserLibrary.objects.create(user=user)
        login(request, user)
        
        return JsonResponse({
            'message': 'Login successful',
            'username': user.username,
            'is_staff': user.is_staff,
            'library': {
                'bookmarks': library.bookmarks,
                'readHistory': library.read_history,
                'progress': library.progress,
                'saved_words': library.saved_words # ✨ ADD THIS
            }
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

# 3. LOGIN API
def api_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            library, created = UserLibrary.objects.get_or_create(user=user)
            
            return JsonResponse({
                'message': 'Login successful',
                'username': user.username,
                'is_staff': user.is_staff,
                'library': {
                    'bookmarks': library.bookmarks,
                    'readHistory': library.read_history,
                    'progress': library.progress,
                    'saved_words': library.saved_words
                }
            })
        else:
            return JsonResponse({'error': 'Invalid username or password'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

# 4. LOGOUT API
def api_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# 5. SAVE PROGRESS API
def api_save_progress(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        
        data = json.loads(request.body)
        library, created = UserLibrary.objects.get_or_create(user=request.user)
        library.bookmarks = data.get('bookmarks', library.bookmarks)
        library.read_history = data.get('readHistory', library.read_history)
        library.progress = data.get('progress', library.progress)
        
        # ✨ ADD THIS LINE: Save the new vocabulary list back to the database
        library.saved_words = data.get(
            'saved_words',
            data.get('savedWords', library.saved_words)
        )
        
        library.save()
        return JsonResponse({'message': 'Progress saved successfully'})

# 6. GET NOVELS API (✨ BULLETPROOF FIX ✨)
def api_get_novels(request):
    novels = Novel.objects.all()
    mangas_data = []

    for novel in novels:
        chapters = novel.chapters.all()
        chapter_dict = {}
        latest_chapter = 0

        for ch in chapters:
            content = ch.content if ch.content else ""
            chapter_dict[str(ch.chapter_number)] = content.split('\n\n')
            if ch.chapter_number > latest_chapter:
                latest_chapter = ch.chapter_number

        cover_url = None
        if novel.cover_image and novel.cover_image.name:
            try:
                cover_url = novel.cover_image.url
            except ValueError:
                # Fallback to a default image or log the issue
                cover_url = '/static/myapp/images/default-cover.jpg'
        
        try:
            safe_rating = float(novel.rating) if novel.rating is not None else 0.0
        except (ValueError, TypeError):
            safe_rating = 0.0

        manga = {
            "id": novel.id + 10000, 
            "title": novel.title or "Untitled",
            "genre": novel.genre or "Generic",
            "ch": latest_chapter, 
            "rating": safe_rating,
            "badge": novel.badge or None,
            "color": novel.color or "linear-gradient(135deg,#1a0533,#3d0a6b,#ff3c5f)",
            "kanji": novel.kanji or "本",
            "coverUrl": cover_url,
            "chapters": chapter_dict
        }
        mangas_data.append(manga)

    return JsonResponse(mangas_data, safe=False)

# ==========================================
# ADMIN DASHBOARD APIs
# ==========================================

@staff_member_required(login_url='/')
def api_admin_add_novel(request):
    if request.method == 'POST':
        try:
            # ✨ WE USE request.POST HERE SO IT CAN ACCEPT FILES! ✨
            rating_val = request.POST.get('rating', '0.0')
            if not rating_val: 
                rating_val = '0.0'

            title = request.POST.get('title', 'Untitled')
            genre = request.POST.get('genre', 'Generic')
            
            novel = Novel.objects.create(
                title=title,
                genre=genre,
                rating=float(rating_val),
                badge=request.POST.get('badge') or None,
                color=request.POST.get('color', 'linear-gradient(135deg,#1a0533,#3d0a6b,#ff3c5f)'),
                kanji=request.POST.get('kanji', '本')
            )
            
            # ✨ CATCH AND SAVE THE ACTUAL IMAGE FILE! ✨
            if 'cover_image' in request.FILES:
                novel.cover_image = request.FILES['cover_image']
                novel.save()

            cover_url = novel.cover_image.url if novel.cover_image and hasattr(novel.cover_image, 'url') else None

            # Log the activity
            actor = request.user.username if request.user.is_authenticated else 'Admin'
            ActivityLog.log_activity(
                action='novel_created',
                description=f'Created new novel "<strong>{title}</strong>" ({genre})',
                actor=actor,
                novel_title=title,
                novel_id=novel.id
            )

            return JsonResponse({'message': 'Novel created!', 'id': novel.id + 10000, 'coverUrl': cover_url}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_add_chapter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # ✨ THE FIX: Subtract the 10000 offset so it matches the real Database ID! ✨
            raw_novel_id = int(data.get('novel'))
            real_novel_id = raw_novel_id - 10000 
            
            novel = Novel.objects.get(id=real_novel_id)
            chapter_number = data.get('chapter_number')
            
            chapter = Chapter.objects.create(
                novel=novel,
                chapter_number=chapter_number,
                content=data.get('content', '')
            )
            
            # Log the activity
            actor = request.user.username if request.user.is_authenticated else 'Admin'
            ActivityLog.log_activity(
                action='chapter_created',
                description=f'Added Chapter <strong>{chapter_number}</strong> to "<strong>{novel.title}</strong>"',
                actor=actor,
                novel_title=novel.title,
                novel_id=novel.id,
                chapter_number=chapter_number
            )
            
            return JsonResponse({'message': 'Chapter added successfully', 'id': chapter.id}, status=201)
        except Novel.DoesNotExist:
            return JsonResponse({'error': 'Novel not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_get_users(request):
    if request.method == 'GET':
        users = User.objects.all().values('id', 'username', 'email', 'date_joined', 'is_active')
        users_list = list(users)
        for u in users_list:
            u['date_joined'] = u['date_joined'].strftime('%Y-%m-%d') if u['date_joined'] else None
        return JsonResponse(users_list, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_get_libraries(request):
    if request.method == 'GET':
        libraries = UserLibrary.objects.select_related('user').all()
        lib_data = []
        for lib in libraries:
            lib_data.append({
                'user': lib.user.username,
                'bookmarks': lib.bookmarks,
                'read_history': lib.read_history,
                'progress': lib.progress
            })
        return JsonResponse(lib_data, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_update_user(request, user_id):
    """Update user information (username, email)"""
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=user_id)
            
            old_username = user.username
            old_email = user.email
            
            # Update fields if provided
            if 'username' in data:
                new_username = data['username'].strip()
                if new_username and new_username != user.username:
                    if User.objects.filter(username=new_username).exists():
                        return JsonResponse({'error': 'Username already exists'}, status=400)
                    user.username = new_username
            
            if 'email' in data:
                new_email = data['email'].strip()
                if new_email and new_email != user.email:
                    if User.objects.filter(email=new_email).exists():
                        return JsonResponse({'error': 'Email already in use'}, status=400)
                    user.email = new_email
            
            user.save()
            
            # Log the activity if changes were made
            if old_username != user.username or old_email != user.email:
                actor = request.user.username if request.user.is_authenticated else 'Admin'
                ActivityLog.log_activity(
                    action='user_updated',
                    description=f'Updated user "<strong>{user.username}</strong>" (username/email changed)',
                    actor=actor,
                    novel_title=user.username
                )
            
            return JsonResponse({
                'message': 'User updated successfully',
                'id': user.id,
                'username': user.username,
                'email': user.email
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_toggle_ban(request, user_id):
    """Ban or unban a user by toggling is_active"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_active = data.get('is_active')  # True to unban, False to ban
            
            user = User.objects.get(id=user_id)
            user.is_active = is_active
            user.save()
            
            action = 'unbanned' if is_active else 'banned'
            
            # Log the activity
            actor = request.user.username if request.user.is_authenticated else 'Admin'
            ActivityLog.log_activity(
                action='user_banned' if not is_active else 'user_unbanned',
                description=f'<strong>{action.capitalize()}</strong> user "<strong>{user.username}</strong>"',
                actor=actor,
                novel_title=user.username
            )
            
            return JsonResponse({
                'message': f'User {action} successfully',
                'id': user.id,
                'username': user.username,
                'is_active': user.is_active
            })
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==========================================
# INDEX PAGE DYNAMIC DATA APIs
# ==========================================

def _novel_to_dict(novel, latest_chapter=0, latest_chapter_time=None):
    """Helper function to convert a Novel to a dictionary for API responses"""
    cover_url = None
    if novel.cover_image:
        try:
            cover_url = novel.cover_image.url
        except Exception:
            pass
    
    try:
        safe_rating = float(novel.rating) if novel.rating is not None else 0.0
    except (ValueError, TypeError):
        safe_rating = 0.0
    
    return {
        "id": novel.id + 10000,
        "title": novel.title or "Untitled",
        "genre": novel.genre or "Generic",
        "ch": latest_chapter,
        "rating": safe_rating,
        "badge": novel.badge or None,
        "color": novel.color or "linear-gradient(135deg,#1a0533,#3d0a6b,#ff3c5f)",
        "kanji": novel.kanji or "本",
        "coverUrl": cover_url,
        "position": novel.position or "center",
        "is_featured": novel.is_featured,
    }


def api_get_featured(request):
    """Get featured novels (admin selected via is_featured checkbox)"""
    # Get novels marked as featured, limit to 2
    featured_novels = Novel.objects.filter(is_featured=True)[:2]
    featured_data = []
    
    for novel in featured_novels:
        chapters = novel.chapters.all()
        latest_chapter = 0
        for ch in chapters:
            if ch.chapter_number > latest_chapter:
                latest_chapter = ch.chapter_number
        
        featured_data.append(_novel_to_dict(novel, latest_chapter))
    
    return JsonResponse(featured_data, safe=False)


def api_get_popular(request):
    """Get popular novels (all novels, ordered by rating)"""
    # Get ALL novels, ordered by rating descending
    popular_novels = Novel.objects.all().order_by('-rating')
    popular_data = []
    
    for novel in popular_novels:
        chapters = novel.chapters.all()
        latest_chapter = 0
        for ch in chapters:
            if ch.chapter_number > latest_chapter:
                latest_chapter = ch.chapter_number
        
        popular_data.append(_novel_to_dict(novel, latest_chapter))
    
    return JsonResponse(popular_data, safe=False)


def api_get_rankings(request):
    """Get top ranked novels (only novels with rating 9-10, limited to 10)"""
    # Get novels with rating >= 9.0, ordered by rating descending, limit to 10
    ranked_novels = Novel.objects.filter(rating__gte=9.0).order_by('-rating')[:10]
    rankings_data = []
    
    for novel in ranked_novels:
        chapters = novel.chapters.all()
        latest_chapter = 0
        for ch in chapters:
            if ch.chapter_number > latest_chapter:
                latest_chapter = ch.chapter_number
        
        rankings_data.append(_novel_to_dict(novel, latest_chapter))
    
    return JsonResponse(rankings_data, safe=False)


def api_get_updates(request):
    """Get latest updates (all novels with chapters, ordered by most recent)"""
    # Get ALL novels that have chapters
    novel_ids_with_updates = Chapter.objects.values_list('novel_id', flat=True).distinct()
    
    # Get the latest chapter info for each novel
    updates_data = []
    processed_novel_ids = set()  # Track processed novels to avoid duplicates
    
    for novel_id in novel_ids_with_updates:
        # Skip if already processed (extra safety against duplicates)
        if novel_id in processed_novel_ids:
            continue
        
        try:
            novel = Novel.objects.get(id=novel_id)
            chapters = novel.chapters.all()
            latest_chapter = 0
            latest_time = None
            
            for ch in chapters:
                if ch.chapter_number > latest_chapter:
                    latest_chapter = ch.chapter_number
                    latest_time = ch.created_at
            
            novel_dict = _novel_to_dict(novel, latest_chapter)
            
            # Add time info
            if latest_time:
                time_diff = timezone.now() - latest_time
                if time_diff.days > 0:
                    novel_dict['time'] = f"{time_diff.days}d ago"
                elif time_diff.seconds // 3600 > 0:
                    novel_dict['time'] = f"{time_diff.seconds // 3600}h ago"
                else:
                    novel_dict['time'] = f"{time_diff.seconds // 60}m ago"
            else:
                novel_dict['time'] = 'Recently'
            
            updates_data.append(novel_dict)
            processed_novel_ids.add(novel_id)  # Mark as processed
            
        except Novel.DoesNotExist:
            # Skip novels that might have been deleted
            continue
    
    # Sort by time (most recent first) - using the time field
    updates_data.sort(key=lambda x: x.get('time', 'Recently'))
    
    return JsonResponse(updates_data[:10], safe=False)  # Limit to 10


def api_get_new_releases(request):
    """Get new releases (all novels, ordered by creation date)"""
    # Get ALL novels, ordered by creation date descending
    new_novels = Novel.objects.all().order_by('-created_at')
    new_releases_data = []
    
    for novel in new_novels:
        chapters = novel.chapters.all()
        latest_chapter = 0
        for ch in chapters:
            if ch.chapter_number > latest_chapter:
                latest_chapter = ch.chapter_number
        
        novel_dict = _novel_to_dict(novel, latest_chapter)
        
        # Add creation time info
        time_diff = timezone.now() - novel.created_at
        if time_diff.days > 0:
            novel_dict['time'] = f"{time_diff.days}d ago"
        elif time_diff.seconds // 3600 > 0:
            novel_dict['time'] = f"{time_diff.seconds // 3600}h ago"
        else:
            novel_dict['time'] = f"{time_diff.seconds // 60}m ago"
        
        new_releases_data.append(novel_dict)
    
    return JsonResponse(new_releases_data, safe=False)


@staff_member_required(login_url='/')
def api_admin_toggle_featured(request, novel_id):
    """Toggle featured status for a novel"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_featured = data.get('is_featured', False)
            
            # If setting to featured, check if we already have 2 featured novels
            if is_featured:
                current_featured = Novel.objects.filter(is_featured=True).count()
                if current_featured >= 2:
                    return JsonResponse({'error': 'Maximum 2 featured novels allowed'}, status=400)
            
            novel = Novel.objects.get(id=novel_id)
            novel.is_featured = is_featured
            novel.save()
            
            # Log the activity
            actor = request.user.username if request.user.is_authenticated else 'Admin'
            action_type = 'novel_featured' if is_featured else 'novel_unfeatured'
            ActivityLog.log_activity(
                action=action_type,
                description=f'<strong>{"Featured" if is_featured else "Unfeatured"}</strong> novel "<strong>{novel.title}</strong>"',
                actor=actor,
                novel_title=novel.title,
                novel_id=novel.id
            )
            
            return JsonResponse({
                'message': f'Novel {"featured" if is_featured else "unfeatured"} successfully',
                'id': novel.id,
                'is_featured': novel.is_featured
            })
        except Novel.DoesNotExist:
            return JsonResponse({'error': 'Novel not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_delete_novel(request, novel_id):
    """Delete a novel and all its chapters"""
    if request.method == 'DELETE':
        try:
            # ✨ Subtract the 10000 offset to get real database ID! ✨
            real_novel_id = novel_id - 10000
            
            novel = Novel.objects.get(id=real_novel_id)
            novel_title = novel.title
            
            # Log the activity BEFORE deletion
            actor = request.user.username if request.user.is_authenticated else 'Admin'
            ActivityLog.log_activity(
                action='novel_deleted',
                description=f'Deleted novel "<strong>{novel_title}</strong>"',
                actor=actor,
                novel_title=novel_title,
                novel_id=real_novel_id
            )
            
            novel.delete()
            
            return JsonResponse({'message': 'Novel deleted successfully'})
        except Novel.DoesNotExist:
            return JsonResponse({'error': 'Novel not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_get_featured(request):
    """Get current featured novels for admin management"""
    if request.method == 'GET':
        featured = Novel.objects.filter(is_featured=True)
        all_novels = Novel.objects.all().order_by('-created_at')
        
        featured_data = []
        for novel in featured:
            chapters = novel.chapters.all()
            latest_chapter = 0
            for ch in chapters:
                if ch.chapter_number > latest_chapter:
                    latest_chapter = ch.chapter_number
            
            featured_data.append(_novel_to_dict(novel, latest_chapter))
        
        all_data = []
        for novel in all_novels:
            chapters = novel.chapters.all()
            latest_chapter = 0
            for ch in chapters:
                if ch.chapter_number > latest_chapter:
                    latest_chapter = ch.chapter_number
            
            all_data.append(_novel_to_dict(novel, latest_chapter))
        
        return JsonResponse({
            'featured': featured_data,
            'all_novels': all_data
        }, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required(login_url='/')
def api_admin_get_activities(request):
    """Get recent activity log for the admin dashboard"""
    if request.method == 'GET':
        limit = request.GET.get('limit', 20)
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 20
        
        activities = ActivityLog.get_recent_activities(limit)
        
        activities_data = []
        for activity in activities:
            # Calculate relative time
            time_diff = timezone.now() - activity.timestamp
            if time_diff.seconds < 60:
                time_ago = 'Just now'
            elif time_diff.seconds < 3600:
                minutes = time_diff.seconds // 60
                time_ago = f'{minutes} minute{"s" if minutes != 1 else ""} ago'
            elif time_diff.seconds < 86400:
                hours = time_diff.seconds // 3600
                time_ago = f'{hours} hour{"s" if hours != 1 else ""} ago'
            elif time_diff.days < 7:
                time_ago = f'{time_diff.days} day{"s" if time_diff.days != 1 else ""} ago'
            else:
                time_ago = activity.timestamp.strftime('%b %d, %Y')
            
            # Determine dot color based on action type
            action_color_map = {
                'novel_created': 'green',
                'novel_updated': 'cyan',
                'novel_deleted': 'red',
                'novel_featured': 'purple',
                'novel_unfeatured': 'purple',
                'chapter_created': 'cyan',
                'chapter_deleted': 'red',
                'user_created': 'green',
                'user_updated': 'cyan',
                'user_banned': 'red',
                'user_unbanned': 'green',
                'system': 'purple',
            }
            color = action_color_map.get(activity.action, 'purple')
            
            activities_data.append({
                'id': activity.id,
                'action': activity.action,
                'description': activity.description,
                'actor': activity.actor or 'Admin',
                'novel_title': activity.novel_title or '',
                'timestamp': time_ago,
                'color': color,
            })
        
        return JsonResponse(activities_data, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)
