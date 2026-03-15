from django.urls import path

from . import views

app_name = 'skillswap'

# URL routes for the SkillSwap app
urlpatterns = [
    # Home page
    path('', views.HomeView.as_view(), name='home'),

    # User registration
    path('register/', views.register_view, name='register'),

    # Main dashboard after login
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Profile pages
    path('profiles/<str:username>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),

    # Block or unblock a user, and view blocked users
    path('block/<str:username>/', views.block_toggle, name='block-toggle'),
    path('blocked/', views.blocked_list, name='blocked-list'),

    # Skill management
    path('skills/', views.my_skills_view, name='my-skills'),
    path('skills/add/', views.user_skill_create, name='user-skill-add'),
    path('skills/<int:pk>/edit/', views.user_skill_update, name='user-skill-edit'),
    path('skills/<int:pk>/delete/', views.user_skill_delete, name='user-skill-delete'),

    # Request management
    path('requests/', views.MyRequestListView.as_view(), name='my-requests'),
    path('requests/add/', views.request_create, name='request-add'),
    path('requests/<int:pk>/', views.RequestDetailView.as_view(), name='request-detail'),
    path('requests/<int:pk>/bookmark/', views.bookmark_toggle, name='request-bookmark'),
    path('requests/<int:pk>/edit/', views.request_update, name='request-edit'),
    path('requests/<int:pk>/close/', views.request_close, name='request-close'),

    # Bookmark list
    path('bookmarks/', views.bookmark_list, name='bookmarks'),

    # Notification pages
    path('notifications/', views.notification_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification-read'),

    # Inbox and messaging
    path('inbox/', views.inbox_list, name='inbox'),
    path('inbox/<int:match_id>/', views.inbox_detail, name='inbox-detail'),
    path('inbox/<int:match_id>/send/', views.inbox_send, name='inbox-send'),

    # Report related pages
    path('report/', views.report_form, name='report'),
    path('report/request/<int:pk>/', views.report_request, name='report-request'),
    path('report/profile/<str:username>/', views.report_profile, name='report-profile'),
    path('report/message/<int:pk>/', views.report_message, name='report-message'),
    path('my-reports/', views.my_reports, name='my-reports'),
    path('moderation/reports/', views.moderation_reports, name='mod-reports'),

    # Explore and recommendation pages
    path('explore/requests/', views.ExploreRequestListView.as_view(), name='explore-requests'),
    path('explore/users/', views.ExploreUserListView.as_view(), name='explore-users'),
    path('recommendations/', views.RecommendationListView.as_view(), name='recommendations'),

    # Match related pages
    path('requests/<int:pk>/invite/', views.match_create, name='match-create'),
    path('matches/', views.MatchListView.as_view(), name='match-list'),
    path('matches/<int:pk>/', views.MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:pk>/<str:action>/', views.match_action, name='match-action'),
    path('matches/<int:pk>/feedback/', views.feedback_create, name='feedback-create'),
]