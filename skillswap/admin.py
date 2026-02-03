from django.contrib import admin

from .models import Feedback, Match, Profile, Request, Skill, UserSkill


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_mode', 'location', 'avatar')
    search_fields = ('user__username', 'location')
    filter_horizontal = ('bookmarked_requests',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name', 'category')


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'type', 'level', 'created_at')
    list_filter = ('type', 'level')
    search_fields = ('user__username', 'skill__name')


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'skill', 'status', 'created_at')
    list_filter = ('status', 'skill__category')
    search_fields = ('title', 'description', 'user__username')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('request', 'requester', 'partner', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('request__title', 'requester__username', 'partner__username')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('match', 'rater', 'ratee', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('match__request__title', 'rater__username', 'ratee__username')
