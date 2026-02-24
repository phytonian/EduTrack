"""
EduTrack Core Signals
Automated notifications and profile management.
NOTE: UserProfile creation signal is also in models.py — 
      signals.py is the canonical location, models.py version is a safety net.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone


# Import models lazily to avoid circular imports
def get_models():
    from .models import (
        UserProfile, Student, Assignment, Submission,
        Attendance, Comment, Holiday, StatusPost,
        AssignmentTicket, BrushUpRequest, TestScore,
        Notification, Feedback
    )
    return (UserProfile, Student, Assignment, Submission,
            Attendance, Comment, Holiday, StatusPost,
            AssignmentTicket, BrushUpRequest, TestScore,
            Notification, Feedback)


# =====================
# USER PROFILE — auto-create on user creation
# =====================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when a new user is registered."""
    if created:
        UserProfile, *_ = get_models()
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'student'})


# =====================
# ASSIGNMENT — notify students and auto-create submission records
# =====================

@receiver(post_save, sender='core.Assignment')
def on_assignment_created(sender, instance, created, **kwargs):
    """
    When a new active assignment is created:
    1. Create 'not_submitted' Submission records for all students.
    2. Send notifications to all students.
    """
    if not created or instance.status != 'active':
        return

    _, Student, _, Submission, _, _, _, _, _, _, _, Notification, _ = get_models()

    students = Student.objects.all().select_related('user')

    submissions_to_create = []
    notifications_to_create = []

    for student in students:
        if not Submission.objects.filter(assignment=instance, student=student).exists():
            submissions_to_create.append(
                Submission(assignment=instance, student=student, status='not_submitted')
            )
        notifications_to_create.append(
            Notification(
                user=student.user,
                notification_type='assignment',
                title='New Assignment Posted',
                message=f'"{instance.title}" — Due: {instance.due_date}',
                link=f'/student/assignment/{instance.id}/',
            )
        )

    if submissions_to_create:
        Submission.objects.bulk_create(submissions_to_create, ignore_conflicts=True)
    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)


# =====================
# SUBMISSION — notify teacher when submitted; notify student when graded
# =====================

@receiver(post_save, sender='core.Submission')
def on_submission_updated(sender, instance, created, **kwargs):
    """Notify teacher on submission; notify student on grading."""
    _, _, _, _, _, _, _, _, _, _, _, Notification, _ = get_models()

    if not created and instance.status == 'graded' and instance.graded_by:
        # Notify the student
        Notification.objects.create(
            user=instance.student.user,
            notification_type='grade',
            title='Assignment Graded',
            message=f'Your submission for "{instance.assignment.title}" has been graded. '
                    f'Score: {instance.score}/{instance.assignment.max_score}',
            link=f'/student/assignment/{instance.assignment.id}/',
        )

    elif instance.status == 'submitted':
        # Notify the teacher who owns the assignment
        teacher = instance.assignment.created_by
        Notification.objects.get_or_create(
            user=teacher,
            notification_type='assignment',
            title='New Submission',
            message=f'{instance.student.user.get_full_name()} submitted "{instance.assignment.title}"',
            link=f'/teacher/submission/{instance.id}/',
        )


# =====================
# HOLIDAY — notify all users when broadcast
# (Additional signal — primary notification is in the view)
# =====================

@receiver(post_save, sender='core.Holiday')
def on_holiday_created(sender, instance, created, **kwargs):
    """Already handled in HolidayBroadcastView — this is a safety net."""
    pass


# =====================
# COMMENT — notify target user
# =====================

@receiver(post_save, sender='core.Comment')
def on_comment_posted(sender, instance, created, **kwargs):
    if not created or instance.is_private:
        return
    _, _, _, _, _, _, _, _, _, _, _, Notification, _ = get_models()
    Notification.objects.create(
        user=instance.target_user,
        notification_type='comment',
        title='New Comment',
        message=f'{instance.author.get_full_name()} posted a comment on your profile.',
        link=f'/comments/{instance.target_user.id}/',
    )


# =====================
# BRUSHUP REQUEST — notify teacher when student requests
# =====================

@receiver(post_save, sender='core.BrushUpRequest')
def on_brushup_requested(sender, instance, created, **kwargs):
    if not created:
        return
    _, _, _, _, _, _, _, _, _, _, _, Notification, _ = get_models()
    teacher = instance.topic.created_by
    Notification.objects.create(
        user=teacher,
        notification_type='brushup',
        title='New Brush-Up Request',
        message=f'{instance.student.user.get_full_name()} requested '
                f'{instance.get_request_type_display()} for "{instance.topic.title}".',
        link=f'/teacher/brushup-requests/',
    )
