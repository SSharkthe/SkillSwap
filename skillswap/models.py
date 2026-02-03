from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    class PreferredMode(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'
        BOTH = 'both', 'Both'

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
    bookmarked_requests = models.ManyToManyField(
        'Request',
        blank=True,
        related_name='bookmarked_by',
    )

    def __str__(self):
        return f"Profile for {self.user.username}"

    def get_absolute_url(self):
        return reverse('skillswap:profile-detail', kwargs={'username': self.user.username})


class Skill(models.Model):
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
    class SkillType(models.TextChoices):
        OFFER = 'offer', 'Offer'
        WANT = 'want', 'Want'

    class SkillLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_skills')
    type = models.CharField(max_length=10, choices=SkillType.choices)
    level = models.CharField(max_length=12, choices=SkillLevel.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'skill', 'type'], name='unique_user_skill_type'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.skill.name} ({self.type})"


class Request(models.Model):
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
            models.CheckConstraint(condition=~Q(requester=models.F('partner')), name='requester_not_partner'),
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


class Feedback(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='feedback')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedback')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['match', 'rater'], name='unique_feedback_per_match_rater'),
            models.CheckConstraint(condition=~Q(rater=models.F('ratee')), name='rater_not_ratee'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.rater} to {self.ratee} ({self.rating})"
