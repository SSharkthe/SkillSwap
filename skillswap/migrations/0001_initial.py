from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
                    'user',
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('category', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'category')},
            },
        ),
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
                    'skill',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests',
                                      to='skillswap.skill'),
                ),
                (
                    'user',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests',
                                      to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
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
                    'skill',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_skills',
                                      to='skillswap.skill'),
                ),
                (
                    'user',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_skills',
                                      to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
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
                    'partner',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partner_matches',
                                      to=settings.AUTH_USER_MODEL),
                ),
                (
                    'request',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches',
                                      to='skillswap.request'),
                ),
                (
                    'requester',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_matches',
                                      to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='userskill',
            constraint=models.UniqueConstraint(fields=('user', 'skill', 'type'), name='unique_user_skill_type'),
        ),
        migrations.AddConstraint(
            model_name='match',
            constraint=models.CheckConstraint(condition=~Q(requester=models.F('partner')),
                                              name='requester_not_partner'),
        ),
        migrations.AddConstraint(
            model_name='match',
            constraint=models.UniqueConstraint(
                condition=Q(status='pending'),
                fields=('request', 'requester', 'partner'),
                name='unique_pending_match',
            ),
        ),
    ]
