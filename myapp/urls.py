from django.urls import path
from . import views

urlpatterns = [
    # The main frontend page
    path('', views.home, name='home'),
    
    # Custom Admin Dashboard
    path('custom-admin/', views.custom_admin, name='custom_admin'),

    # The Backend API endpoints
    path('api/register/', views.api_register, name='api_register'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/save-progress/', views.api_save_progress, name='api_save_progress'),
    path('api/novels/', views.api_get_novels, name='api_get_novels'),

    # Admin Dashboard APIs
    path('api/admin/novels/create/', views.api_admin_add_novel, name='admin_add_novel'),
    path('api/admin/chapters/create/', views.api_admin_add_chapter, name='admin_add_chapter'),
    path('api/admin/novels/<int:novel_id>/chapters/<int:chapter_number>/delete/', views.api_admin_delete_chapter, name='admin_delete_chapter'),
    path('api/admin/users/', views.api_admin_get_users, name='admin_get_users'),
    path('api/admin/users/<int:user_id>/update/', views.api_admin_update_user, name='admin_update_user'),
    path('api/admin/users/<int:user_id>/toggle-ban/', views.api_admin_toggle_ban, name='admin_toggle_ban'),
    path('api/admin/libraries/', views.api_admin_get_libraries, name='admin_get_libraries'),
    
    # Index Page Dynamic Data APIs
    path('api/featured/', views.api_get_featured, name='api_get_featured'),
    path('api/popular/', views.api_get_popular, name='api_get_popular'),
    path('api/rankings/', views.api_get_rankings, name='api_get_rankings'),
    path('api/updates/', views.api_get_updates, name='api_get_updates'),
    path('api/new-releases/', views.api_get_new_releases, name='api_get_new_releases'),
    
    # Admin Homepage Management APIs
    path('api/admin/featured/', views.api_admin_get_featured, name='admin_get_featured'),
    path('api/admin/hero-slots/', views.api_admin_get_hero_slots, name='admin_get_hero_slots'),
    path('api/admin/novels/<int:novel_id>/hero-slot/', views.api_admin_set_hero_slot, name='admin_set_hero_slot'),
    path('api/admin/novels/<int:novel_id>/toggle-featured/', views.api_admin_toggle_featured, name='admin_toggle_featured'),
    
    # Admin Delete Novel API
    path('api/admin/novels/<int:novel_id>/delete/', views.api_admin_delete_novel, name='admin_delete_novel'),
    
    # Admin Activity Log API
    path('api/admin/activities/', views.api_admin_get_activities, name='admin_get_activities'),
]
