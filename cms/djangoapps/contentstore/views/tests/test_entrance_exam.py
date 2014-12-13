"""
Test module for Entrance Exams AJAX callback handler workflows
"""
from django.contrib.auth.models import User

from contentstore.tests.utils import AjaxEnabledTestClient, CourseTestCase
from milestones import api as milestones_api
from models.settings.course_metadata import CourseMetadata


class EntranceExamHandlerTests(CourseTestCase):
    """
    Base test class for create, save, and delete
    """
    def setUp(self):
        """
        Shared scaffolding for individual test runs
        """
        super(EntranceExamHandlerTests, self).setUp()
        self.course_key = self.course.id
        self.usage_key = self.course.location
        self.course_url = '/course/{}'.format(unicode(self.course.id))
        self.exam_url = '/course/{}/entrance_exam/'.format(unicode(self.course.id))

    def test_contentstore_views_entrance_exam_post(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_post
        """
        resp = self.client.post(self.exam_url, {}, http_accept='application/json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(self.exam_url)
        self.assertEqual(resp.status_code, 200)
        metadata = CourseMetadata.fetch_all(self.course)
        self.assertTrue(metadata['entrance_exam_enabled'])
        self.assertIsNotNone(metadata['entrance_exam_minimum_score_pct'])
        self.assertIsNotNone(metadata['entrance_exam_id'])
        self.assertTrue(len(milestones_api.get_course_milestones(unicode(self.course.id))))

    def test_contentstore_views_entrance_exam_get(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_get
        """
        resp = self.client.post(self.exam_url, {}, http_accept='application/json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(self.exam_url)
        self.assertEqual(resp.status_code, 200)

    def test_contentstore_views_entrance_exam_delete(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_delete
        """
        resp = self.client.post(self.exam_url, {}, http_accept='application/json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(self.exam_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.delete(self.exam_url)
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get(self.exam_url)
        self.assertEqual(resp.status_code, 404)

        user = User.objects.create(
            username='test_user',
            email='test_user@edx.org',
            is_active=True,
        )
        user.set_password('test')
        user.save()
        paths = milestones_api.get_course_milestones_fulfillment_paths(
            unicode(self.course_key),
            user.__dict__
        )

        # What we have in this case is a course milestone requirement with no valid fulfillment
        # paths for the specified user.  The LMS is likely going to have to ignore this situation,
        # because we can't confidently prevent this from occuring at some point in the future.
        self.assertEqual(len(paths['milestone_1']), 0)

        # Re-adding an entrance exam to the course should fix the missing link
        resp = self.client.post(self.exam_url, {}, http_accept='application/json')
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(self.exam_url)
        self.assertEqual(resp.status_code, 200)

    def test_contentstore_views_entrance_exam_delete_bogus_course(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_delete_bogus_course
        """
        resp = self.client.delete('/course/bad/course/key/entrance_exam')
        self.assertEqual(resp.status_code, 400)

    def test_contentstore_views_entrance_exam_get_bogus_course(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_get_bogus_course
        """
        resp = self.client.get('/course/bad/course/key/entrance_exam')
        self.assertEqual(resp.status_code, 400)

    def test_contentstore_views_entrance_exam_post_bogus_course(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_post_bogus_course
        """
        resp = self.client.post(
            '/course/bad/course/key/entrance_exam',
            {},
            http_accept='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_contentstore_views_entrance_exam_post_invalid_http_accept(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_post_invalid_http_accept
        """
        resp = self.client.post(
            '/course/bad/course/key/entrance_exam',
            {},
            http_accept='text/html'
        )
        self.assertEqual(resp.status_code, 400)

    def test_contentstore_views_entrance_exam_get_invalid_user(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_get_invalid_user
        """
        user = User.objects.create(
            username='test_user',
            email='test_user@edx.org',
            is_active=True,
        )
        user.set_password('test')
        user.save()
        self.client = AjaxEnabledTestClient()
        self.client.login(username='test_user', password='test')
        resp = self.client.get(self.exam_url)
        self.assertEqual(resp.status_code, 403)

    def test_contentstore_views_entrance_exam_unsupported_method(self):
        """
        Unit Test: test_contentstore_views_entrance_exam_unsupported_method
        """
        resp = self.client.put(self.exam_url)
        self.assertEqual(resp.status_code, 405)
