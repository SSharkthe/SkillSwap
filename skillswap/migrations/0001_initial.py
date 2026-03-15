from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    # This is the first migration for the app
    initial = True

    # Depend on the user model so foreign keys can be created correctly
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Profile model stores extra user information
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True)),
                ('availability', models.CharField(blank=True, max_length=200)),
                (
                    'preferred_mode',
                    models.CharField(
                        choices=[('online', 'Online'), ('offline', 'Offline'), ('both', 'Both')],
                        default='both',
                        max_length=10,
                    ),
                ),
                ('location', models.CharField(blank=True, max_length=120)),
                (
                    # One user has one profile
                    'user',
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),

        # Skill model stores all available skills in the system
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('category', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                # Show skills in alphabetical order
                'ordering': ['name'],
                # Avoid duplicate skill names in the same category
                'unique_together': {('name', 'category')},
            },
        ),

        # Request model represents a user's help request
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=160)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'status',
                    models.CharField(
                        choices=[('open', 'Open'), ('closed', 'Closed')],
                        default='open',
                        max_length=10,
                    ),
                ),
                ('preferred_time', models.CharField(blank=True, max_length=120)),
                (
                    # Each request is linked to one skill
                    'skill',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests',
                                      to='skillswap.skill'),
                ),
                (
                    # The user who created the request
                    'user',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests',
                                      to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                # Newest requests appear first
                'ordering': ['-created_at'],
            },
        ),

        # UserSkill connects users with skills they offer or want
        migrations.CreateModel(
            name='UserSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('offer', 'Offer'), ('want', 'Want')], max_length=10)),
                (
                    'level',
                    models.CharField(
                        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
                        max_length=12,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    # Skill connected to this user-skill record
                    'skill',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_skills',
                                      to='skillswap.skill'),
                ),
                (
                    # User connected to this user-skill record
                    'user',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_skills',
                                      to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # Match model stores matching records between requester and partner
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pending'),
                            ('accepted', 'Accepted'),
                            ('rejected', 'Rejected'),
                            ('completed', 'Completed'),
                        ],
                        default='pending',
                        max_length=12,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    # The user who may help with the request
                    'partner',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partner_matches',
                                      to=settings.AUTH_USER_MODEL),
                ),
                (
                    # The request being matched
                    'request',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches',
                                      to='skillswap.request'),
                ),
                (
                    # The user who created the original request
                    'requester',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_matches',
                                      to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # Prevent duplicate user-skill-type combinations
        migrations.AddConstraint(
            model_name='userskill',
            constraint=models.UniqueConstraint(fields=('user', 'skill', 'type'), name='unique_user_skill_type'),
        ),

        # Make sure a user cannot match with themselves
        migrations.AddConstraint(
            model_name='match',
            constraint=models.CheckConstraint(condition=~Q(requester=models.F('partner')),
                                              name='requester_not_partner'),
        ),

        # Only one pending match is allowed for the same request/requester/partner
        migrations.AddConstraint(
            model_name='match',
            constraint=models.UniqueConstraint(
                condition=Q(status='pending'),
                fields=('request', 'requester', 'partner'),
                name='unique_pending_match',
            ),
        ),
    ]