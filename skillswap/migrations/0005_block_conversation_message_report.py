from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    # This migration depends on contenttypes and the previous skillswap migration
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('skillswap', '0004_notifications_through_activity'),
    ]

    operations = [
        # Block model stores user blocking relationships
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # User who is being blocked
                ('blocked', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_by',
                                              to=settings.AUTH_USER_MODEL)),
                # User who made the block action
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks_made',
                                              to=settings.AUTH_USER_MODEL)),
            ],
            options={
                # Show newest blocks first
                'ordering': ['-created_at'],
            },
        ),

        # Conversation model creates one chat room for each match
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # Each match has one conversation
                ('match', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='conversation',
                                               to='skillswap.match')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # Message model stores chat messages inside a conversation
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(max_length=2000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # Used to mark whether the message has been read
                ('is_read', models.BooleanField(default=False)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages',
                                                   to='skillswap.conversation')),
                # User who sent the message
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages',
                                             to=settings.AUTH_USER_MODEL)),
            ],
            options={
                # Messages should appear in time order
                'ordering': ['created_at'],
            },
        ),

        # Report model is used for reporting users or related content
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Generic object id for the reported content
                ('object_id', models.PositiveIntegerField()),
                ('reason', models.CharField(choices=[('spam', 'Spam'), ('harassment', 'Harassment'), ('scam', 'Scam'),
                                                     ('inappropriate', 'Inappropriate'), ('other', 'Other')],
                                            max_length=20)),
                # Optional extra details from the reporter
                ('details', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[('open', 'Open'), ('reviewing', 'Reviewing'), ('resolved', 'Resolved'),
                             ('dismissed', 'Dismissed')], default='open', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                # Admin or reviewer can leave a note here
                ('resolution_note', models.TextField(blank=True)),
                # Used with object_id for generic relation
                ('content_type',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                # User being reported, if applicable
                ('reported_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                    related_name='reports_received', to=settings.AUTH_USER_MODEL)),
                # User who submitted the report
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports_made',
                                               to=settings.AUTH_USER_MODEL)),
                # User who reviewed the report
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='reports_reviewed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                # Newest reports first for easier review
                'ordering': ['-created_at'],
            },
        ),

        # Prevent duplicate block records between the same two users
        migrations.AddConstraint(
            model_name='block',
            constraint=models.UniqueConstraint(fields=('blocker', 'blocked'), name='unique_block'),
        ),

        # A user should not be able to block themselves
        migrations.AddConstraint(
            model_name='block',
            constraint=models.CheckConstraint(condition=~models.Q(blocker=models.F('blocked')), name='no_self_block'),
        ),
    ]