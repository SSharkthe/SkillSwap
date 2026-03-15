from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, Q
from django.urls import reverse

User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    # User preference for how they want to learn or interact
    class PreferredMode(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'
        BOTH = 'both', 'Both'

    # Basic profile information linked to one user
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    availability = models.CharField(max_length=200, blank=True)
    preferred_mode = models.CharField(
        max_length=10,
        choices=PreferredMode.choices,
        default=PreferredMode.BOTH,
    )
    location = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Skills are connected through UserSkill so we can store extra info
    skills = models.ManyToManyField(
        'Skill',
        through='UserSkill',
        through_fields=('profile', 'skill'),
        related_name='profiles',
        blank=True,
    )

    # Requests that the user has bookmarked
    bookmarked_requests = models.ManyToManyField(
        'Request',
        blank=True,
        related_name='bookmarked_by',
    )

    # Used to track recent activity in the system
    last_active = models.DateTimeField(null=True, blank=True)
    last_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

    def get_absolute_url(self):
        return reverse('skillswap:profile-detail', kwargs={'username': self.user.username})


class Block(models.Model):
    # Stores block relationships between users
    blocker = models.ForeignKey(User, related_name="blocks_made", on_delete=models.CASCADE)
    blocked = models.ForeignKey(User, related_name="blocked_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Prevent duplicate block records
            models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_block"),
            # A user should not be able to block themselves
            models.CheckConstraint(condition=~Q(blocker=F("blocked")), name="no_self_block"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


class Skill(models.Model):
    # Different categories for skills
    class Category(models.TextChoices):
        PROGRAMMING = 'programming', 'Programming'
        ART = 'art', 'Art'
        LANGUAGE = 'language', 'Language'
        MUSIC = 'music', 'Music'
        SPORTS = 'sports', 'Sports'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=120)
    category = models.CharField(
        max_length=120,
        choices=Category.choices,
        default=Category.OTHER,
    )
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('name', 'category')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category})"

    # Returns a Bootstrap icon name based on the skill category
    def category_icon(self):
        return {
            self.Category.PROGRAMMING: 'bi-code-slash',
            self.Category.ART: 'bi-palette',
            self.Category.LANGUAGE: 'bi-translate',
            self.Category.MUSIC: 'bi-music-note-beamed',
            self.Category.SPORTS: 'bi-trophy',
            self.Category.OTHER: 'bi-tag',
        }.get(self.category, 'bi-tag')


class UserSkill(models.Model):
    # Whether the user offers this skill or wants to learn it
    class SkillType(models.TextChoices):
        OFFER = 'offer', 'Offer'
        WANT = 'want', 'Want'

    # User's level for a skill
    class SkillLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='profile_skills',
        null=True,
        blank=True,
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_skills')
    type = models.CharField(max_length=10, choices=SkillType.choices)
    level = models.CharField(max_length=12, choices=SkillLevel.choices)

    # Extra information about the skill
    learning_months = models.PositiveSmallIntegerField(null=True, blank=True)
    self_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # One user can only have one record for the same skill and type
            models.UniqueConstraint(fields=['user', 'skill', 'type'], name='unique_user_skill_type'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.skill.name} ({self.type})"

    def save(self, *args, **kwargs):
        # Automatically connect the profile if it was not set manually
        if self.profile is None and self.user_id:
            self.profile = self.user.profile
        super().save(*args, **kwargs)


class Request(models.Model):
    # Current status of a learning/help request
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='requests')
    title = models.CharField(max_length=160)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    preferred_time = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title}"

    def get_absolute_url(self):
        return reverse('skillswap:request-detail', kwargs={'pk': self.pk})


class Match(models.Model):
    # Status for a match between requester and partner
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='matches')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_matches')
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partner_matches')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # The requester and partner cannot be the same user
            models.CheckConstraint(condition=~Q(requester=models.F('partner')), name='requester_not_partner'),
            # Only one pending match is allowed for the same request-user pair
            models.UniqueConstraint(
                fields=['request', 'requester', 'partner'],
                condition=Q(status='pending'),
                name='unique_pending_match',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request.title} ({self.requester} -> {self.partner})"

    def get_absolute_url(self):
        return reverse('skillswap:match-detail', kwargs={'pk': self.pk})


class Conversation(models.Model):
    # Each match has one conversation
    match = models.OneToOneField(Match, related_name="conversation", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Conversation for {self.match}"


class Message(models.Model):
    # Messages belong to a conversation and have a sender
    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender} at {self.created_at:%Y-%m-%d %H:%M}"


class Feedback(models.Model):
    # Feedback is given after a match between two users
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='feedback')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedback')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # One user can only leave feedback once per match
            models.UniqueConstraint(fields=['match', 'rater'], name='unique_feedback_per_match_rater'),
            # A user cannot rate themselves
            models.CheckConstraint(condition=~Q(rater=models.F('ratee')), name='rater_not_ratee'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.rater} to {self.ratee} ({self.rating})"


class Report(models.Model):
    # Possible reasons when reporting content or a user
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        HARASSMENT = "harassment", "Harassment"
        SCAM = "scam", "Scam"
        INAPPROPRIATE = "inappropriate", "Inappropriate"
        OTHER = "other", "Other"

    # Review status of a report
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_made")
    reported_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_received",
    )

    # Generic relation allows reporting different model objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    # Admin or reviewer information
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report {self.pk} by {self.reporter}"


class Notification(models.Model):
    # Different actions that can create a notification
    class Verb(models.TextChoices):
        INVITE_SENT = 'invite_sent', 'Invite sent'
        INVITE_ACCEPTED = 'invite_accepted', 'Invite accepted'
        INVITE_REJECTED = 'invite_rejected', 'Invite rejected'
        MATCH_COMPLETED = 'match_completed', 'Match completed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='acted_notifications')
    match = models.ForeignKey('Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    request = models.ForeignKey('Request', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='notifications')
    verb = models.CharField(max_length=30, choices=Verb.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user} ({self.verb})"


def is_blocked(user_a, user_b) -> bool:
    # Return False directly if one of the users is missing
    if not user_a or not user_b:
        return False

    # Check both directions: a blocks b or b blocks a
    return Block.objects.filter(
        Q(blocker=user_a, blocked=user_b) | Q(blocker=user_b, blocked=user_a)
    ).exists()


def blocked_user_ids(user):
    # Anonymous users do not have block relationships
    if not user or not getattr(user, "is_authenticated", False):
        return []

    # Users this person blocked
    blocked_ids = Block.objects.filter(blocker=user).values_list("blocked_id", flat=True).order_by()
    # Users who blocked this person
    blocker_ids = Block.objects.filter(blocked=user).values_list("blocker_id", flat=True).order_by()

    # Merge both querysets into one list of related blocked user ids
    return list(blocked_ids.union(blocker_ids))