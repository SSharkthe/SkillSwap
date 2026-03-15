from django.db.models import Q

from .models import Message, Notification


def unread_notifications(request):
    """Expose unread notification count to all templates."""
    # Only check notifications for logged-in users
    if request.user.is_authenticated:
        return {
            "unread_notifications_count": Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count()
        }
    # Guests should see 0 unread notifications
    return {"unread_notifications_count": 0}


def unread_messages(request):
    # Only count unread messages for authenticated users
    if request.user.is_authenticated:
        return {
            "unread_messages_count": Message.objects.filter(
                # Find messages in conversations where the current user is one of the two matched users
                Q(conversation__match__partner=request.user) | Q(conversation__match__requester=request.user),
                is_read=False,
            )
            # Do not count messages sent by the current user
            .exclude(sender=request.user)
            .count()
        }
    # Guests should see 0 unread messages
    return {"unread_messages_count": 0}