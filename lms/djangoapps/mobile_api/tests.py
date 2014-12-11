"""
Tests for mobile API utilities
"""

import ddt
from mock import patch
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.factories import UserFactory
from student import auth

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .utils import mobile_access_when_enrolled

ROLE_CASES = (
    (auth.CourseBetaTesterRole, True),
    (auth.CourseStaffRole, True),
    (auth.CourseInstructorRole, True),
    (None, False)
)


class MobileAPITestCase(ModuleStoreTestCase, APITestCase):
    """
    Base class for testing Mobile APIs
    """
    def setUp(self):
        super(MobileAPITestCase, self).setUp()
        self.course = CourseFactory.create(mobile_available=True)
        self.user = UserFactory.create()
        self.password = 'test'
        self.username = self.user.username

    def tearDown(self):
        super(MobileAPITestCase, self).tearDown()
        self.client.logout()

    def login(self):
        """
        login test user
        """
        self.client.login(username=self.username, password=self.password)

    def enroll(self, course):
        """
        enroll test user in test course
        """
        resp = self.client.post(reverse('change_enrollment'), {
            'enrollment_action': 'enroll',
            'course_id': course.id.to_deprecated_string(),
            'check_access': True,
        })
        self.assertEqual(resp.status_code, 200)


@ddt.ddt
class TestMobileApiUtils(MobileAPITestCase):
    """
    Tests for mobile API utilities
    """
    @ddt.data(*ROLE_CASES)
    @ddt.unpack
    def test_mobile_role_access(self, role, should_have_access):
        """
        Verifies that our mobile access function properly handles using roles to grant access
        """
        non_mobile_course = CourseFactory.create(mobile_available=False)
        if role:
            role(non_mobile_course.id).add_users(self.user)
        self.assertEqual(should_have_access, mobile_access_when_enrolled(non_mobile_course, self.user))

    def test_mobile_explicit_access(self):
        """
        Verifies that our mobile access function listens to the mobile_available flag as it should
        """
        self.assertTrue(mobile_access_when_enrolled(self.course, self.user))

    def test_missing_course(self):
        """
        Verifies that we handle the case where a course doesn't exist
        """
        self.assertFalse(mobile_access_when_enrolled(None, self.user))

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_unreleased_course(self):
        """
        Verifies that we handle the case where a course hasn't started
        """
        self.assertFalse(mobile_access_when_enrolled(self.course, self.user))
