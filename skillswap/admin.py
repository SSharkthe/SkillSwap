from django.contrib import admin

from .models import Block, Conversation, Feedback, Match, Message, Notification, Profile, Report, Request, Skill, \
    UserSkill


# Admin config for user profiles
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Fields shown in the admin list page
    list_display = ('user', 'preferred_mode', 'location', 'avatar')
    search_fields = ('user__username', 'location')
    # Better UI for many-to-many bookmarked requests
    filter_horizontal = ('bookmarked_requests',)


# Admin config for skills
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name', 'category')


# Admin config for user skills
@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'type', 'level', 'created_at')
    list_filter = ('type', 'level')
    search_fields = ('user__username', 'skill__name')


# Admin config for requests
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'skill', 'status', 'created_at')
    list_filter = ('status', 'skill__category')
    search_fields = ('title', 'description', 'user__username')


# Admin config for matches
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('request', 'requester', 'partner', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('request__title', 'requester__username', 'partner__username')


# Admin config for feedback records
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('match', 'rater', 'ratee', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('match__request__title', 'rater__username', 'ratee__username')


# Admin config for notifications
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verb', 'is_read', 'created_at')
    list_filter = ('is_read', 'verb')
    search_fields = ('user__username', 'actor__username', 'message')


# Admin config for block relations
@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__username', 'blocked__username')
    list_filter = ('created_at',)


# Admin config for conversations
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('match', 'created_at')
    search_fields = ('match__request__title', 'match__requester__username', 'match__partner__username')


# Admin config for messages
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'body')


# Admin config for reports
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'reported_user', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason')
    search_fields = ('reporter__username', 'reported_user__username')
    # Custom actions for quickly updating report status
    actions = ('mark_resolved', 'mark_dismissed')

    @admin.action(description='Mark selected reports resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(status=Report.Status.RESOLVED)

    @admin.action(description='Mark selected reports dismissed')
    def mark_dismissed(self, request, queryset):
        queryset.update(status=Report.Status.DISMISSED)