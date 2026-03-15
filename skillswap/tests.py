from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from django.utils import timezone

from .models import Block, Conversation, Feedback, Match, Message, Notification, Report, Request, Skill, UserSkill

User = get_user_model()


class SkillSwapTests(TestCase):
    def setUp(self):
        # Create some basic test data used in many test cases
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')
        self.skill = Skill.objects.create(name='Python', category='programming')

    def test_registration_creates_profile(self):
        # Test that registering a new user also creates a profile automatically
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
        # Logged-in user should be able to update profile info
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
        # Same user should not be able to create duplicate skill records with same type
        UserSkill.objects.create(user=self.user, skill=self.skill, type='offer', level='beginner')
        with self.assertRaises(IntegrityError):
            UserSkill.objects.create(user=self.user, skill=self.skill, type='offer', level='beginner')

    def test_request_create_and_owner_permissions(self):
        # User can create a request and becomes its owner
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

        # Another user should not be able to edit someone else's request
        self.client.logout()
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('skillswap:request-edit', args=[request_obj.pk]))
        self.assertEqual(response.status_code, 404)

    def test_match_flow(self):
        # Create a request first so another user can send a match invite
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

        # Requester should not be allowed to accept their own invite
        response = self.client.post(reverse('skillswap:match-action', args=[match.pk, 'accept']))
        self.assertEqual(response.status_code, 403)

        # Partner accepts the match
        self.client.logout()
        self.client.login(username='bob', password='password123')
        response = self.client.post(reverse('skillswap:match-action', args=[match.pk, 'accept']))
        self.assertEqual(response.status_code, 302)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.ACCEPTED)

        # Partner completes the match
        response = self.client.post(reverse('skillswap:match-action', args=[match.pk, 'complete']))
        self.assertEqual(response.status_code, 302)
        match.refresh_from_db()
        self.assertEqual(match.status, Match.Status.COMPLETED)

    def test_recommendations_login_required(self):
        # Recommendation page should require login
        response = self.client.get(reverse('skillswap:recommendations'))
        self.assertEqual(response.status_code, 302)

    def test_recommendations_overlap_and_ordering(self):
        # Prepare more skills and user-skill data for recommendation logic
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

        # Current user should not appear in their own recommendations
        self.assertNotIn(self.user, recommendations)
        self.assertIn(self.other, recommendations)
        self.assertIn(charlie, recommendations)
        self.assertNotIn(dana, recommendations)

        # User with more matched skills should rank higher
        self.assertEqual(recommendations[0], charlie)
        self.assertGreaterEqual(recommendations[0].final_score, recommendations[1].final_score)

    def test_feedback_permissions_and_constraints(self):
        # Build a match first for feedback testing
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

        # Unrelated user should not be allowed to leave feedback
        self.client.login(username='eve', password='password123')
        response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 5})
        self.assertEqual(response.status_code, 403)

        # Match participants still cannot leave feedback before completion
        self.client.logout()
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 5})
        self.assertEqual(response.status_code, 403)

        # After completion, feedback should be allowed
        match.status = Match.Status.COMPLETED
        match.save(update_fields=['status'])
        response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 4})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Feedback.objects.filter(match=match, rater=self.user).count(), 1)

        # Same user should not create duplicate feedback for the same match
        response = self.client.post(reverse('skillswap:feedback-create', args=[match.pk]), {'rating': 5})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Feedback.objects.filter(match=match, rater=self.user).count(), 1)

    def test_profile_rating_summary(self):
        # Test if profile page shows correct feedback summary
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
        # Bookmark action should redirect anonymous users to login
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
        # Bookmark button should toggle add/remove behavior
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
        # Each user should only see their own bookmarks
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

    def test_notification_created_on_match_invite(self):
        # Creating a match invite should create a notification for the partner
        request_obj = Request.objects.create(
            user=self.other,
            skill=self.skill,
            title='Need Python help',
            description='Functions and classes',
            status='open',
        )
        self.client.login(username='alice', password='password123')
        self.client.post(reverse('skillswap:match-create', args=[request_obj.pk]))
        notification = Notification.objects.get(user=self.other, verb=Notification.Verb.INVITE_SENT)
        self.assertIn('match invite', notification.message)

    def test_notification_created_on_match_accept(self):
        # Accepting a match should notify the requester
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
            status=Match.Status.PENDING,
        )
        self.client.login(username='bob', password='password123')
        self.client.post(reverse('skillswap:match-action', args=[match.pk, 'accept']))
        self.assertTrue(
            Notification.objects.filter(user=self.user, verb=Notification.Verb.INVITE_ACCEPTED).exists()
        )

    def test_notification_visibility_and_mark_read(self):
        # User should only see their own notifications
        notification = Notification.objects.create(
            user=self.user,
            actor=self.other,
            verb=Notification.Verb.INVITE_SENT,
            message='Test notification',
        )
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('skillswap:notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test notification')

        self.client.logout()
        self.client.login(username='bob', password='password123')
        response = self.client.get(reverse('skillswap:notifications'))
        self.assertNotContains(response, 'Test notification')

        # Owner can mark the notification as read
        self.client.logout()
        self.client.login(username='alice', password='password123')
        self.client.post(reverse('skillswap:notification-read', args=[notification.pk]))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_userskill_through_profile(self):
        # Test extra fields stored in the through model
        user_skill = UserSkill.objects.create(
            user=self.user,
            profile=self.user.profile,
            skill=self.skill,
            type='offer',
            level='beginner',
            learning_months=12,
            self_rating=4,
        )
        self.assertEqual(user_skill.learning_months, 12)
        self.assertEqual(user_skill.self_rating, 4)
        self.assertIn(self.skill, self.user.profile.skills.all())

    def test_activity_middleware_updates_last_active(self):
        # Visiting a page should update profile activity info
        self.client.login(username='alice', password='password123')
        self.client.get(reverse('skillswap:dashboard'))
        self.user.profile.refresh_from_db()
        self.assertIsNotNone(self.user.profile.last_active)
        self.assertEqual(self.user.profile.last_path, reverse('skillswap:dashboard'))
        self.assertLessEqual(self.user.profile.last_active, timezone.now())

    def test_password_change_requires_login(self):
        # Password change page should not be accessible without login
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 302)

    def test_password_change_page_for_logged_in_user(self):
        # Logged-in user can access password change page
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)

    def test_block_toggle_requires_login(self):
        # Block action should require login
        response = self.client.post(reverse('skillswap:block-toggle', args=[self.other.username]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_block_toggle_creates_and_deletes(self):
        # Block toggle should create block first, then remove it on next click
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('skillswap:block-toggle', args=[self.other.username]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Block.objects.filter(blocker=self.user, blocked=self.other).exists())

        response = self.client.post(reverse('skillswap:block-toggle', args=[self.other.username]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Block.objects.filter(blocker=self.user, blocked=self.other).exists())

    def test_explore_lists_exclude_blocked_users(self):
        # Blocked users and their requests should not appear in explore pages
        Block.objects.create(blocker=self.user, blocked=self.other)
        other_request = Request.objects.create(
            user=self.other,
            skill=self.skill,
            title='Need Python help',
            description='Functions and classes',
            status='open',
        )
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('skillswap:explore-users'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.other, list(response.context['users']))

        response = self.client.get(reverse('skillswap:explore-requests'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_request, list(response.context['requests']))

    def test_match_invite_blocked_forbidden(self):
        # Match invite should be forbidden if users blocked each other
        request_obj = Request.objects.create(
            user=self.other,
            skill=self.skill,
            title='Need Python help',
            description='Functions and classes',
            status='open',
        )
        Block.objects.create(blocker=self.user, blocked=self.other)
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('skillswap:match-create', args=[request_obj.pk]))
        self.assertEqual(response.status_code, 403)

    def test_conversation_created_on_accept(self):
        # Accepting a match should create a conversation automatically
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
            status=Match.Status.PENDING,
        )
        self.client.login(username='bob', password='password123')
        self.client.post(reverse('skillswap:match-action', args=[match.pk, 'accept']))
        self.assertTrue(Conversation.objects.filter(match=match).exists())

    def test_inbox_permissions_and_message_send(self):
        # Only match participants should be able to access inbox and send messages
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
        conversation = Conversation.objects.create(match=match)
        self.client.login(username='alice', password='password123')
        response = self.client.post(
            reverse('skillswap:inbox-send', args=[match.pk]),
            {'body': 'Hello!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(conversation=conversation, sender=self.user).exists())

        self.client.logout()
        eve = User.objects.create_user(username='eve', password='password123')
        self.client.login(username='eve', password='password123')
        response = self.client.get(reverse('skillswap:inbox-detail', args=[match.pk]))
        self.assertEqual(response.status_code, 403)

    def test_blocked_message_send_forbidden(self):
        # Sending messages should be blocked if one user blocked the other
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
        Conversation.objects.create(match=match)
        Block.objects.create(blocker=self.other, blocked=self.user)
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('skillswap:inbox-send', args=[match.pk]), {'body': 'Hello'})
        self.assertEqual(response.status_code, 403)

    def test_inbox_marks_messages_read(self):
        # Opening inbox detail should mark received messages as read
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
        conversation = Conversation.objects.create(match=match)
        message = Message.objects.create(conversation=conversation, sender=self.other, body='Ping')
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('skillswap:inbox-detail', args=[match.pk]))
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_report_creation_and_visibility(self):
        # Users can create reports for content and later view their own reports
        request_obj = Request.objects.create(
            user=self.other,
            skill=self.skill,
            title='Need Python help',
            description='Functions and classes',
            status='open',
        )
        ct = ContentType.objects.get_for_model(Request)
        self.client.login(username='alice', password='password123')
        response = self.client.post(
            f"{reverse('skillswap:report')}?ct={ct.pk}&oid={request_obj.pk}",
            {'reason': Report.Reason.SPAM, 'details': 'Spam content.'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Report.objects.filter(reporter=self.user, object_id=request_obj.pk).exists())

        response = self.client.get(reverse('skillswap:my-reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Spam')

    def test_moderation_requires_staff(self):
        # Moderation page should only be available for staff users
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('skillswap:mod-reports'))
        self.assertEqual(response.status_code, 302)

        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        response = self.client.get(reverse('skillswap:mod-reports'))
        self.assertEqual(response.status_code, 200)