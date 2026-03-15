from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    # This migration depends on the user model and the previous skillswap migration
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('skillswap', '0003_profile_avatar_bookmarks_skill_category'),
    ]

    operations = [
        # Store the last time the user was active
        migrations.AddField(
            model_name='profile',
            name='last_active',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Save the last visited path for simple activity tracking
        migrations.AddField(
            model_name='profile',
            name='last_path',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        # Record how many months the user has been learning a skill
        migrations.AddField(
            model_name='userskill',
            name='learning_months',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        # Link UserSkill to Profile so profile-based skill relations can be used
        migrations.AddField(
            model_name='userskill',
            name='profile',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='profile_skills',
                to='skillswap.profile',
            ),
        ),
        # Let users give themselves a simple rating for a skill
        migrations.AddField(
            model_name='userskill',
            name='self_rating',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[MinValueValidator(1), MaxValueValidator(5)],
            ),
        ),
        # Add many-to-many relation between profile and skill through UserSkill
        migrations.AddField(
            model_name='profile',
            name='skills',
            field=models.ManyToManyField(
                blank=True,
                related_name='profiles',
                through='skillswap.UserSkill',
                through_fields=('profile', 'skill'),
                to='skillswap.skill',
            ),
        ),
        # Create notification model for system actions related to users, requests, and matches
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Verb shows the type of notification event
                ('verb', models.CharField(
                    choices=[
                        ('invite_sent', 'Invite sent'),
                        ('invite_accepted', 'Invite accepted'),
                        ('invite_rejected', 'Invite rejected'),
                        ('match_completed', 'Match completed'),
                    ],
                    max_length=30,
                )),
                ('message', models.TextField()),
                # Used to mark whether the notification has been opened
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # Actor means the user who triggered the notification, if there is one
                ('actor', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='acted_notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
                # Optional related match
                ('match', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='skillswap.match',
                )),
                # Optional related request
                ('request', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='skillswap.request',
                )),
                # The user who receives the notification
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                # Newest notifications should appear first
                'ordering': ['-created_at'],
            },
        ),
    ]