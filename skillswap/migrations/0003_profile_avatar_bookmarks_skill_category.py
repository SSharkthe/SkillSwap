from django.db import migrations, models


class Migration(migrations.Migration):
    # This migration is based on the previous feedback migration
    dependencies = [
        ('skillswap', '0002_feedback'),
    ]

    operations = [
        # Add avatar field so users can upload a profile picture
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
        # Let users bookmark requests they are interested in
        migrations.AddField(
            model_name='profile',
            name='bookmarked_requests',
            field=models.ManyToManyField(blank=True, related_name='bookmarked_by', to='skillswap.request'),
        ),
        # Limit skill categories to a fixed set of choices
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