"""Tests for wafer.talk views."""

import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from wafer.talks.models import Talk, ACCEPTED, REJECTED, PENDING


def create_user(username, superuser=False, perms=()):
    if superuser:
        create = get_user_model().objects.create_superuser
    else:
        create = get_user_model().objects.create_user
    user = create(
        username, '%s@example.com' % username, '%s_password' % username)
    for codename in perms:
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
    if perms:
        user = get_user_model().objects.get(pk=user.pk)
    return user


def create_talk(title, status, username):
    user = create_user(username)
    talk = Talk.objects.create(
        title=title, status=status, corresponding_author_id=user.id)
    talk.authors.add(user)
    talk.save()
    return talk


def mock_avatar_url(self):
    if self.user.email is None:
        return None
    return "avatar-%s" % self.user.email


class UsersTalksTests(TestCase):
    def setUp(self):
        self.talk_a = create_talk("Talk A", ACCEPTED, "author_a")
        self.talk_r = create_talk("Talk R", REJECTED, "author_r")
        self.talk_p = create_talk("Talk P", PENDING, "author_p")
        self.client = Client()

    def test_not_logged_in(self):
        """Test that unauthenticated users only see accepted talks."""
        response = self.client.get('/talks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['talk_list']),
                         set([self.talk_a]))

    def test_admin_user(self):
        """Test that admin users see all talks."""
        create_user('super', superuser=True)
        self.client.login(username='super', password='super_password')
        response = self.client.get('/talks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['talk_list']),
                         set([self.talk_a, self.talk_r, self.talk_p]))

    def test_user_with_view_all(self):
        """Test that users with the view_all permission see all talks."""
        create_user('reviewer', perms=['view_all_talks'])
        self.client.login(username='reviewer', password='reviewer_password')
        response = self.client.get('/talks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['talk_list']),
                         set([self.talk_a, self.talk_r, self.talk_p]))


class TalkViewTests(TestCase):
    def setUp(self):
        self.talk_a = create_talk("Talk A", ACCEPTED, "author_a")
        self.talk_r = create_talk("Talk R", REJECTED, "author_r")
        self.talk_p = create_talk("Talk P", PENDING, "author_p")
        self.client = Client()

    def check_talk_view(self, talk, status_code, auth=None):
        if auth is not None:
            self.client.login(**auth)
        response = self.client.get(
            reverse('wafer_talk', kwargs={'pk': talk.pk}))
        self.assertEqual(response.status_code, status_code)

    def test_view_accepted_not_logged_in(self):
        self.check_talk_view(self.talk_a, 200)

    def test_view_rejected_not_logged_in(self):
        self.check_talk_view(self.talk_r, 403)

    def test_view_pending_not_logged_in(self):
        self.check_talk_view(self.talk_p, 403)

    def test_view_accepted_author(self):
        self.check_talk_view(self.talk_a, 200, auth={
            'username': 'author_a', 'password': 'author_a_password',
        })

    def test_view_rejected_author(self):
        self.check_talk_view(self.talk_r, 200, auth={
            'username': 'author_r', 'password': 'author_r_password',
        })

    def test_view_pending_author(self):
        self.check_talk_view(self.talk_p, 200, auth={
            'username': 'author_p', 'password': 'author_p_password',
        })

    def test_view_accepted_has_view_all_perm(self):
        create_user('reviewer', perms=['view_all_talks'])
        self.check_talk_view(self.talk_a, 200, auth={
            'username': 'reviewer', 'password': 'reviewer_password',
        })

    def test_view_rejected_has_view_all_perm(self):
        create_user('reviewer', perms=['view_all_talks'])
        self.check_talk_view(self.talk_r, 200, auth={
            'username': 'reviewer', 'password': 'reviewer_password',
        })

    def test_view_pending_has_view_all_perm(self):
        create_user('reviewer', perms=['view_all_talks'])
        self.check_talk_view(self.talk_p, 200, auth={
            'username': 'reviewer', 'password': 'reviewer_password',
        })


class TalkUpdateTests(TestCase):
    def setUp(self):
        self.talk_a = create_talk("Talk A", ACCEPTED, "author_a")
        self.talk_r = create_talk("Talk R", REJECTED, "author_r")
        self.talk_p = create_talk("Talk P", PENDING, "author_p")
        self.client = Client()

    def check_talk_update(self, talk, status_code, auth=None):
        if auth is not None:
            self.client.login(**auth)
        response = self.client.get(
            reverse('wafer_talk_edit', kwargs={'pk': talk.pk}))
        self.assertEqual(response.status_code, status_code)
        return response

    def test_update_accepted_not_logged_in(self):
        self.check_talk_update(self.talk_a, 403)

    def test_update_rejected_not_logged_in(self):
        self.check_talk_update(self.talk_r, 403)

    def test_update_pending_not_logged_in(self):
        self.check_talk_update(self.talk_p, 403)

    def test_update_accepted_author(self):
        self.check_talk_update(self.talk_a, 403, auth={
            'username': 'author_a', 'password': 'author_a_password',
        })

    def test_update_rejected_author(self):
        self.check_talk_update(self.talk_r, 403, auth={
            'username': 'author_r', 'password': 'author_r_password',
        })

    def test_update_pending_author(self):
        self.check_talk_update(self.talk_p, 200, auth={
            'username': 'author_p', 'password': 'author_p_password',
        })

    def test_update_accepted_superuser(self):
        create_user('super', superuser=True)
        self.check_talk_update(self.talk_a, 200, auth={
            'username': 'super', 'password': 'super_password',
        })

    def test_update_rejected_superuser(self):
        create_user('super', superuser=True)
        self.check_talk_update(self.talk_r, 200, auth={
            'username': 'super', 'password': 'super_password',
        })

    def test_update_pending_superuser(self):
        create_user('super', superuser=True)
        self.check_talk_update(self.talk_p, 200, auth={
            'username': 'super', 'password': 'super_password',
        })

    def test_corresponding_author_displayed(self):
        response = self.check_talk_update(self.talk_p, 200, auth={
            'username': 'author_p', 'password': 'author_p_password',
        })
        self.assertContains(response, (
            '<p>Submitted by <a href="/users/author_p/">author_p</a>.</p>'),
            html=True)


class SpeakerTests(TestCase):
    def setUp(self):
        self.talk_a = create_talk("Talk A", ACCEPTED, "author_a")
        self.talk_r = create_talk("Talk R", REJECTED, "author_r")
        self.talk_p = create_talk("Talk P", PENDING, "author_p")
        self.client = Client()

    @mock.patch('wafer.users.models.UserProfile.avatar_url', mock_avatar_url)
    def test_view_one_speaker(self):
        img = self.talk_a.corresponding_author.userprofile.avatar_url()
        response = self.client.get(
            reverse('wafer_talks_speakers'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "\n".join([
            '<div class="container">',
            '<div class="row">',
            '    <div class="col-md-3">',
            '        <img class="thumbnail center-block" src="%s">' % img,
            '        <h3 class="text-center">author_a</h3>',
            '    </div>',
            '</div>',
            '</div>',
        ]), html=True)

    def check_n_speakers(self, n, expected_rows):
        self.talk_a.delete()
        talks = []
        for i in range(n):
            talks.append(create_talk("Talk %d" % i, ACCEPTED, "author_%d" % i))
        profiles = [t.corresponding_author.userprofile for t in talks]

        response = self.client.get(
            reverse('wafer_talks_speakers'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["speaker_rows"], [
            profiles[start:end] for start, end in expected_rows
        ])

    @mock.patch('wafer.users.models.UserProfile.avatar_url', mock_avatar_url)
    def test_view_three_speakers(self):
        self.check_n_speakers(3, [(0, 3)])

    @mock.patch('wafer.users.models.UserProfile.avatar_url', mock_avatar_url)
    def test_view_four_speakers(self):
        self.check_n_speakers(4, [(0, 4)])

    @mock.patch('wafer.users.models.UserProfile.avatar_url', mock_avatar_url)
    def test_view_five_speakers(self):
        self.check_n_speakers(5, [(0, 4), (4, 5)])

    @mock.patch('wafer.users.models.UserProfile.avatar_url', mock_avatar_url)
    def test_view_seven_speakers(self):
        self.check_n_speakers(7, [(0, 4), (4, 7)])
