from django.conf import settings

from courseware.access import has_access
from milestones.api import get_course_milestones_fulfillment_paths
from student.models import CourseEnrollment
from xmodule.tabs import CourseTabList


def get_course_tab_list(course, user):
    user_is_enrolled = user.is_authenticated() and CourseEnrollment.is_enrolled(user, course.id)
    xmodule_tab_list = CourseTabList.iterate_displayable(
        course,
        settings,
        user.is_authenticated(),
        has_access(user, 'staff', course, course.id),
        user_is_enrolled
    )

    # Entrance Exams Feature
    # If the course has an entrance exam, we'll need to see if the user has not passed it
    # If so, we'll need to hide away all of the tabs except for Courseware and Instructor
    entrance_exam_mode = False
    if settings.FEATURES.get('ENTRANCE_EXAMS', False) and settings.FEATURES.get('MILESTONES_APP', False):
        if getattr(course, 'entrance_exam_enabled', False):
            course_milestones_paths = get_course_milestones_fulfillment_paths(
                unicode(course.id),
                user.__dict__
            )
            for __, value in course_milestones_paths.iteritems():
                if len(value.get('content', [])):
                    for content in value['content']:
                        if content['content_id'] == course.entrance_exam_id:
                            entrance_exam_mode = True
                            break

    # Now that we've loaded the tabs for this course, perform the Entrance Exam mode work
    # Majority case is no entrance exam defined
    if not entrance_exam_mode:
        course_tab_list = xmodule_tab_list
    # Hide all of the tabs except for 'Courseware', and rename 'Courseware' to 'Entrance Exam'
    # We also always return the 'Instructor' tab
    else:
        course_tab_list = []
        for tab in xmodule_tab_list:
            if tab.type not in ['courseware', 'instructor']:
                continue
            if tab.type == 'courseware':
                tab.name = "Entrance Exam"
            course_tab_list.append(tab)
    return course_tab_list
