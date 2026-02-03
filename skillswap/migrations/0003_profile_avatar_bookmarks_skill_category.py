from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('skillswap', '0002_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
        migrations.AddField(
            model_name='profile',
            name='bookmarked_requests',
            field=models.ManyToManyField(blank=True, related_name='bookmarked_by', to='skillswap.request'),
        ),
        migrations.AlterField(
            model_name='skill',
            name='category',
            field=models.CharField(
                choices=[
                    ('programming', 'Programming'),
                    ('art', 'Art'),
                    ('language', 'Language'),
                    ('music', 'Music'),
                    ('sports', 'Sports'),
                    ('other', 'Other'),
                ],
                default='other',
                max_length=120,
            ),
        ),
    ]
