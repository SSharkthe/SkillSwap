from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Feedback, Match, Request, Skill, UserSkill

User = get_user_model()


class SkillSwapTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')
        self.skill = Skill.objects.create(name='Python', category='programming')

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

        def test_recommendations_login_required(self):
            response = self.client.get(reverse('skillswap:recommendations'))
            self.assertEqual(response.status_code, 302)

        def test_recommendations_overlap_and_ordering(self):
            skill_two = Skill.objects.create(name='Django', category='programming')
            skill_three = Skill.objects.create(name='Data Analysis', category='other')

            UserSkill.objects.create(user=self.user, skill=self.skill, type='want', level='beginner')
            UserSkill.objects.create(user=self.user, skill=skill_two, type='want', level='beginner')

            charlie = User.objects.create_user(username='charlie', password='password123')
            dana = User.objects.create_user(username='dana', password='password123')

            UserSkill.objects.create(user=self.other, skill=self.skill, type='offer', level='advanced')
            UserSkill.objects.create(user=charlie, skill=self.skill, type='offer', level='advanced')
            UserSkill.objects.create(user=charlie, skill=skill_two, type='offer', level='advanced')
            UserSkill.objects.create(user=dana, skill=skill_three, type='offer', level='advanced')

            self.client.login(username='alice', password='password123')
            response = self.client.get(reverse('skillswap:recommendations'))
            self.assertEqual(response.status_code, 200)
            recommendations = list(response.context['recommendations'])
            self.assertNotIn(self.user, recommendations)
            self.assertIn(self.other, recommendations)
            self.assertIn(charlie, recommendations)
            self.assertNotIn(dana, recommendations)
            self.assertEqual(recommendations[0], charlie)

        def test_feedback_permissions_and_constraints(self):
            request_obj = Request.objects.create(
                user=self.other,
                skill=self.skill,
                title='Need Python help',
                description='Functions and classes',
                status='open',
            )
            match = Match.objects.create(
                request=request_obj,
                requester=self.user,
                partner=self.other,
                status=Match.Status.ACCEPTED,
            )
            User.objects.create_user(username='eve', password='password123')

            self.client.login(username='eve', password='password123')
            response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 5})
            self.assertEqual(response.status_code, 403)

            self.client.logout()
            self.client.login(username='alice', password='password123')
            response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 5})
            self.assertEqual(response.status_code, 403)

            match.status = Match.Status.COMPLETED
            match.save(update_fields=['status'])
            response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 4})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Feedback.objects.filter(match=match, rater=self.user).count(), 1)
            response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 5})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Feedback.objects.filter(match=match, rater=self.user).count(), 1)

        def test_profile_rating_summary(self):
            request_obj = Request.objects.create(
                user=self.other,
                skill=self.skill,
                title='Need Python help',
                description='Functions and classes',
                status='open',
            )
            match = Match.objects.create(
                request=request_obj,
                requester=self.user,
                partner=self.other,
                status=Match.Status.COMPLETED,
            )
            Feedback.objects.create(match=match, rater=self.user, ratee=self.other, rating=4, comment='Great session')

            self.client.login(username='alice', password='password123')
            response = self.client.get(reverse('skillswap:profile-detail', args=[self.other.username]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['rating_summary']['count'], 1)
            self.assertAlmostEqual(response.context['rating_summary']['average'], 4)

        def test_bookmark_toggle_requires_login(self):
            request_obj = Request.objects.create(
                user=self.other,
                skill=self.skill,
                title='Need Python help',
                description='Functions and classes',
                status='open',
            )
            response = self.client.post(reverse('skillswap:request-bookmark', args=[request_obj.pk]))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response.url)

        def test_bookmark_toggle_adds_and_removes(self):
            request_obj = Request.objects.create(
                user=self.other,
                skill=self.skill,
                title='Need Python help',
                description='Functions and classes',
                status='open',
            )
            self.client.login(username='alice', password='password123')
            response = self.client.post(reverse('skillswap:request-bookmark', args=[request_obj.pk]))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(self.user.profile.bookmarked_requests.filter(pk=request_obj.pk).exists())

            response = self.client.post(reverse('skillswap:request-bookmark', args=[request_obj.pk]))
            self.assertEqual(response.status_code, 302)
            self.assertFalse(self.user.profile.bookmarked_requests.filter(pk=request_obj.pk).exists())

        def test_bookmark_list_scoped_to_user(self):
            request_obj = Request.objects.create(
                user=self.other,
                skill=self.skill,
                title='Need Python help',
                description='Functions and classes',
                status='open',
            )
            other_request = Request.objects.create(
                user=self.user,
                skill=self.skill,
                title='Need Java help',
                description='Basics',
                status='open',
            )
            self.user.profile.bookmarked_requests.add(request_obj)
            self.other.profile.bookmarked_requests.add(other_request)

            self.client.login(username='alice', password='password123')
            response = self.client.get(reverse('skillswap:bookmarks'))
            self.assertEqual(response.status_code, 200)
            bookmarks = list(response.context['bookmarks'])
            self.assertIn(request_obj, bookmarks)
            self.assertNotIn(other_request, bookmarks)

        def test_password_change_requires_login(self):
            response = self.client.get(reverse('password_change'))
            self.assertEqual(response.status_code, 302)

        def test_password_change_page_for_logged_in_user(self):
            self.client.login(username='alice', password='password123')
            response = self.client.get(reverse('password_change'))
            self.assertEqual(response.status_code, 200)
