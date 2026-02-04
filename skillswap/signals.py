from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Match, Notification, Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(pre_save, sender=Match)
def capture_match_status(sender, instance, **kwargs):
    if instance.pk:
        instance._previous_status = (
            Match.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .first()
        )
    else:
        instance._previous_status = None


@receiver(post_save, sender=Match)
def notify_match_updates(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.partner,
            actor=instance.requester,
            match=instance,
            request=instance.request,
            verb=Notification.Verb.INVITE_SENT,
            message=f"{instance.requester.username} sent you a match invite for '{instance.request.title}'.",
        )
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status is None or previous_status == instance.status:
        return

    if instance.status == Match.Status.ACCEPTED:
        Notification.objects.create(
            user=instance.requester,
            actor=instance.partner,
            match=instance,
            request=instance.request,
            verb=Notification.Verb.INVITE_ACCEPTED,
            message=f"{instance.partner.username} accepted your match invite for '{instance.request.title}'.",
        )
    elif instance.status == Match.Status.REJECTED:
        Notification.objects.create(
            user=instance.requester,
            actor=instance.partner,
            match=instance,
            request=instance.request,
            verb=Notification.Verb.INVITE_REJECTED,
            message=f"{instance.partner.username} declined your match invite for '{instance.request.title}'.",
        )
    elif instance.status == Match.Status.COMPLETED:
        Notification.objects.create(
            user=instance.requester,
            actor=None,
            match=instance,
            request=instance.request,
            verb=Notification.Verb.MATCH_COMPLETED,
            message=f"The match for '{instance.request.title}' has been marked completed.",
        )
        Notification.objects.create(
            user=instance.partner,
            actor=None,
            match=instance,
            request=instance.request,
            verb=Notification.Verb.MATCH_COMPLETED,
            message=f"The match for '{instance.request.title}' has been marked completed.",
        )
