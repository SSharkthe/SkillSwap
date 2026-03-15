from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    # This migration depends on the initial tables in the skillswap app
    dependencies = [
        ('skillswap', '0001_initial'),
    ]

    operations = [
        # Create the Feedback model for user ratings after a match
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Rating must be between 1 and 5
                ('rating', models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                # Optional short comment from the user
                ('comment', models.CharField(blank=True, max_length=300)),
                # Store when the feedback was created
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # Link feedback to a specific match
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='skillswap.match')),
                # The user who receives the feedback
                ('ratee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_feedback', to=settings.AUTH_USER_MODEL)),
                # The user who gives the feedback
                ('rater', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_feedback', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                # Show newest feedback first
                'ordering': ['-created_at'],
            },
        ),
        # Make sure one user can only leave one feedback per match
        migrations.AddConstraint(
            model_name='feedback',
            constraint=models.UniqueConstraint(fields=('match', 'rater'), name='unique_feedback_per_match_rater'),
        ),
        # A user should not rate themselves
        migrations.AddConstraint(
            model_name='feedback',
            constraint=models.CheckConstraint(condition=~models.Q(rater=models.F('ratee')), name='rater_not_ratee'),
        ),
    ]