from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Match, Request, Skill, UserSkill

User = get_user_model()


class SkillSwapTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')
        self.skill = Skill.objects.create(name='Python', category='Programming')

    def test_registration_creates_profile(self):
        response = self.client.post(
            reverse('skillswap:register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'StrongPassword123',
                'password2': 'StrongPassword123',
            },
        )
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'profile'))

    def test_profile_update(self):
        self.client.login(username='alice', password='password123')
        response = self.client.post(
            reverse('skillswap:profile-edit'),
            {
                'bio': 'Hello',
                'availability': 'Weekdays',
                'preferred_mode': 'online',
                'location': 'Campus',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Hello')

    def test_user_skill_unique_constraint(self):
        UserSkill.objects.create(user=self.user, skill=self.skill, type='offer', level='beginner')
        with self.assertRaises(IntegrityError):
            UserSkill.objects.create(user=self.user, skill=self.skill, type='offer', level='beginner')

    def test_request_create_and_owner_permissions(self):
        self.client.login(username='alice', password='password123')
        response = self.client.post(
            reverse('skillswap:request-add'),
            {
                'skill': self.skill.pk,
                'title': 'Learn Django',
                'description': 'Need help with Django basics',
                'preferred_time': 'Evenings',
                'status': 'open',
            },
        )
        self.assertEqual(response.status_code, 302)
        request_obj = Request.objects.get(title='Learn Django')
        self.assertEqual(request_obj.user, self.user)

        self.client.logout()
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('skillswap:request-edit', args=[request_obj.pk]))
        self.assertEqual(response.status_code, 404)

    def test_match_flow(self):
        request_obj = Request.objects.create(
            user=self.other,
            skill=self.skill,
            title='Need Python help',
            description='Functions and classes',
            status='open',
        )
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('skillswap:match-create', args=[request_obj.pk]))
        self.assertEqual(response.status_code, 302)
        match = Match.objects.get(request=request_obj, requester=self.user, partner=self.other)
        self.assertEqual(match.status, Match.Status.PENDING)

        response = self.client.post(reverse('skillswap:match-action', args=[match.pk, 'accept']))
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.login(username='bob', password='password123')
        response = self.client.post(reverse('skillswap:match-action', args=[match.pk, 'accept']))
        self.assertEqual(response.status_code, 302)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.ACCEPTED)

        response = self.client.post(reverse('skillswap:match-action', args=[match.pk, 'complete']))
        self.assertEqual(response.status_code, 302)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.COMPLETED)