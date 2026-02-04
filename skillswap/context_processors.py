from django.db.models import Q

from .models import Message, Notification


def unread_notifications(request):
    """Expose unread notification count to all templates."""
    if request.user.is_authenticated:
        return {
            "unread_notifications_count": Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count()
        }
    return {"unread_notifications_count": 0}


def unread_messages(request):
    if request.user.is_authenticated:
        return {
            "unread_messages_count": Message.objects.filter(
                Q(conversation__match__partner=request.user) | Q(conversation__match__requester=request.user),
                is_read=False,
            )
            .exclude(sender=request.user)
            .count()
        }
    return {"unread_messages_count": 0}
