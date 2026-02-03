from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('skillswap', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ('comment', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='skillswap.match')),
                ('ratee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_feedback', to=settings.AUTH_USER_MODEL)),
                ('rater', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_feedback', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='feedback',
            constraint=models.UniqueConstraint(fields=('match', 'rater'), name='unique_feedback_per_match_rater'),
        ),
        migrations.AddConstraint(
            model_name='feedback',
            constraint=models.CheckConstraint(check=models.Q(('rater', models.F('ratee')), _negated=True), name='rater_not_ratee'),
        ),
    ]
