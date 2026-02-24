"""
EduTrack Core Models
Complete database models for the Education Management System
Updated: Photo upload, comments, assignment PDF/DOC, roadmap hierarchy, tickets, brush-up
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
import os


# =====================
# VALIDATORS
# =====================

def validate_file_extension(value):
    """Validate file extensions for uploads (PDF, DOC, DOCX)."""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Allowed: {", ".join(valid_extensions)}')


def validate_file_size(value):
    """Validate file size (max 10MB)."""
    filesize = value.size
    if filesize > 10485760:  # 10MB
        raise ValidationError("Maximum file size is 10MB")


def validate_image_extension(value):
    """Validate image file extensions."""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported image format. Allowed: {", ".join(valid_extensions)}')


# =====================
# USER PROFILE MODEL
# =====================

class UserProfile(models.Model):
    """Extended user profile with role-based information and photo upload."""

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text='Contact phone number'
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        null=True,
        blank=True,
        validators=[validate_image_extension],
        help_text='Profile picture (JPG, PNG, GIF)'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, help_text='Residential address')
    pending_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Running total of unpaid/overdue fees (auto-updated)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    def get_photo_url(self):
        """Return profile photo URL or default."""
        if self.profile_photo:
            return self.profile_photo.url
        return '/static/images/default-avatar.png'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

    def is_parent(self):
        return self.role == 'parent'

    def is_admin(self):
        return self.role == 'admin' or self.user.is_superuser


# =====================
# STUDENT MODEL
# =====================

class Student(models.Model):
    """Student model with academic information."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student'
    )
    roll_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        default='',
    )
    grade = models.CharField(max_length=10, help_text='Current grade/class')
    section = models.CharField(max_length=5, help_text='Section (A, B, C, etc.)')
    parent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        limit_choices_to={'profile__role': 'parent'},
        help_text='Parent/Guardian'
    )
    admission_date = models.DateField(default=date.today)
    phone_number = models.CharField(
        max_length=15,
        help_text='Student contact phone number e.g. 9187263541'
    )
    address = models.TextField(
        help_text='Student residential address e.g. Viman Nagar, Pune'
    )
    is_active = models.BooleanField(default=True)
    blood_group = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['grade', 'section', 'roll_number']
        indexes = [
            models.Index(fields=['grade', 'section']),
            models.Index(fields=['roll_number']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"

    def get_full_details(self):
        return f"{self.user.get_full_name()} - Grade {self.grade}{self.section} - {self.roll_number}"

    def get_attendance_rate(self):
        total_days = self.attendance_set.count()
        if total_days == 0:
            return 0
        present_days = self.attendance_set.filter(status='present').count()
        return round((present_days / total_days) * 100, 2)

    def get_average_score(self):
        submissions = self.submission_set.filter(status='graded', score__isnull=False)
        if not submissions.exists():
            return 0
        avg = submissions.aggregate(models.Avg('score'))['score__avg']
        return round(avg, 2) if avg else 0


# =====================
# ASSIGNMENT MODEL
# =====================

class Assignment(models.Model):
    """Assignment/homework model — supports PDF and DOC uploads."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(help_text='Detailed assignment instructions')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assignments'
    )
    subject = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    due_date = models.DateField(help_text='Submission deadline')
    max_score = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    assignment_file = models.FileField(
        upload_to='assignments/',
        null=True,
        blank=True,
        validators=[validate_file_extension, validate_file_size],
        help_text='Assignment file (PDF, DOC, DOCX — max 10MB)'
    )
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} - Due: {self.due_date}"

    def is_overdue(self):
        return self.due_date < date.today() and self.status == 'active'

    def days_until_due(self):
        return (self.due_date - date.today()).days

    def get_submission_stats(self):
        submissions = self.submission_set.all()
        return {
            'total': submissions.count(),
            'submitted': submissions.filter(status__in=['submitted', 'graded']).count(),
            'graded': submissions.filter(status='graded').count(),
            'pending': submissions.filter(status='not_submitted').count(),
        }

    def get_file_extension(self):
        """Return the file extension of uploaded assignment."""
        if self.assignment_file:
            return os.path.splitext(self.assignment_file.name)[1].lower()
        return ''


# =====================
# SUBMISSION MODEL
# =====================

class Submission(models.Model):
    """Student submission for assignments with status tracking."""

    STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('graded', 'Graded'),
        ('resubmit', 'Needs Resubmission'),
        ('late', 'Late Submission'),
    ]

    SUBMISSION_METHOD_CHOICES = [
        ('online', 'Online Upload'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('physical', 'Physical Submission'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submission_set')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_submitted')
    submission_method = models.CharField(max_length=20, choices=SUBMISSION_METHOD_CHOICES, default='online')
    file = models.FileField(
        upload_to='submissions/',
        null=True,
        blank=True,
        validators=[validate_file_size],
        help_text='Submission file (PDF, DOC, DOCX)'
    )
    submission_text = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-submitted_at']),
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}"

    def is_late(self):
        if self.submitted_at and self.assignment.due_date:
            return self.submitted_at.date() > self.assignment.due_date
        return False

    def get_percentage(self):
        if self.score and self.assignment.max_score:
            return round((float(self.score) / self.assignment.max_score) * 100, 2)
        return 0

    def get_grade(self):
        p = self.get_percentage()
        if p >= 90: return 'A+'
        elif p >= 80: return 'A'
        elif p >= 70: return 'B'
        elif p >= 60: return 'C'
        elif p >= 50: return 'D'
        return 'F'


# =====================
# ROADMAP TOPIC MODEL
# =====================

class RoadmapTopic(models.Model):
    """
    Curriculum roadmap topics with full hierarchy (parent/child tree).
    Supports test scheduling and status badges.
    """

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('upcoming', 'Upcoming'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent_topic = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtopics',
        help_text='Parent topic for hierarchy'
    )
    order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roadmap_topics'
    )
    subject = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    estimated_hours = models.IntegerField(null=True, blank=True)
    resources = models.TextField(blank=True)
    test_scheduled = models.DateField(null=True, blank=True, help_text='Scheduled test date')
    test_title = models.CharField(max_length=200, blank=True)
    test_duration = models.IntegerField(null=True, blank=True, help_text='Test duration in minutes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Roadmap Topic'
        verbose_name_plural = 'Roadmap Topics'
        ordering = ['order', 'title']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.title

    def has_upcoming_test(self):
        if self.test_scheduled:
            return self.test_scheduled >= date.today()
        return False

    def get_level(self):
        """Return depth level in hierarchy (0=root, 1=child, etc.)."""
        level = 0
        parent = self.parent_topic
        while parent:
            level += 1
            parent = parent.parent_topic
        return level

    def get_children(self):
        return self.subtopics.all().order_by('order')

    def get_all_descendants(self):
        descendants = []
        for child in self.subtopics.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_badge_class(self):
        """Bootstrap badge class based on status."""
        mapping = {
            'completed': 'bg-success',
            'in_progress': 'bg-warning text-dark',
            'upcoming': 'bg-info',
            'not_started': 'bg-secondary',
        }
        return mapping.get(self.status, 'bg-secondary')


# =====================
# ATTENDANCE MODEL
# =====================

class Attendance(models.Model):
    """Student attendance — teacher marks from dashboard."""

    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('half_day', 'Half Day'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_set')
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marked_attendance')
    notes = models.TextField(
    blank=True,
    help_text='Reason for absence or any relevant note' )
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering = ['-date']
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} - {self.status}"


# =====================
# TEST SCORE MODEL
# =====================

class TestScore(models.Model):
    """Test/exam scores linked to roadmap topics."""

    PASS_THRESHOLD = 50  # percent

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_scores')
    test_name = models.CharField(max_length=200)
    subject = models.CharField(max_length=100, blank=True, default='')
    date = models.DateField()
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade = models.CharField(max_length=5, blank=True)
    remarks = models.TextField(blank=True)
    roadmap_topic = models.ForeignKey(
        RoadmapTopic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_scores'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_test_scores'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Test Score'
        verbose_name_plural = 'Test Scores'
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.test_name} - {self.score}/{self.max_score}"

    def get_percentage(self):
        if self.max_score > 0:
            return round((float(self.score) / float(self.max_score)) * 100, 2)
        return 0

    def is_failed(self):
        return self.get_percentage() < self.PASS_THRESHOLD

    def calculate_grade(self):
        p = self.get_percentage()
        if p >= 90: return 'A+'
        elif p >= 80: return 'A'
        elif p >= 70: return 'B'
        elif p >= 60: return 'C'
        elif p >= 50: return 'D'
        return 'F'


# =====================
# COMMENT MODEL
# =====================

class Comment(models.Model):
    """
    Comments on students, teachers, or parents.
    Admin can comment on all; teachers on student dashboards.
    """

    COMMENT_TYPE_CHOICES = [
        ('student', 'Student Comment'),
        ('teacher', 'Teacher Comment'),
        ('parent', 'Parent Comment'),
        ('general', 'General Comment'),
        ('progress', 'Progress Note'),
        ('behavior', 'Behavior Note'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_made')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_received')
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPE_CHOICES, default='general')
    content = models.TextField()
    is_private = models.BooleanField(default=False, help_text='Visible to admins only')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.get_full_name()} → {self.target_user.get_full_name()}: {self.content[:50]}"


# =====================
# HOLIDAY MODEL
# =====================

class Holiday(models.Model):
    """Holidays and working days — admin broadcasts to all users."""

    HOLIDAY_TYPE_CHOICES = [
        ('holiday', 'Holiday'),
        ('working_day', 'Special Working Day'),
        ('half_day', 'Half Day'),
        ('exam', 'Exam Day'),
    ]

    title = models.CharField(max_length=200)
    date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text='End date for multi-day events')
    description = models.TextField(blank=True)
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPE_CHOICES, default='holiday')
    is_recurring = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_holidays')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        ordering = ['date']

    def __str__(self):
        return f"{self.title} - {self.date}"

    def is_upcoming(self):
        return self.date >= date.today()

    def duration_days(self):
        if self.end_date:
            return (self.end_date - self.date).days + 1
        return 1


# =====================
# STATUS POST MODEL
# =====================

class StatusPost(models.Model):
    """
    Microblogging / status posts by admin.
    Visible on parent and student dashboards.
    """

    TARGET_ROLE_CHOICES = [
        ('all', 'Everyone'),
        ('student', 'Students'),
        ('parent', 'Parents'),
        ('teacher', 'Teachers'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_posts')
    content = models.TextField(max_length=500)
    target_role = models.CharField(max_length=20, choices=TARGET_ROLE_CHOICES, default='all')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Status Post'
        verbose_name_plural = 'Status Posts'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.author.get_full_name()}: {self.content[:50]}"


# =====================
# ASSIGNMENT TICKET MODEL
# =====================

class AssignmentTicket(models.Model):
    """
    Tickets raised by students for offline/non-portal submissions.
    Supports email, WhatsApp, or physical submission methods.
    """

    SUBMISSION_METHOD_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('physical', 'Physical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='tickets')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='tickets')
    submission_method = models.CharField(max_length=20, choices=SUBMISSION_METHOD_CHOICES)
    details = models.TextField(help_text='Details: email sent to, WhatsApp timestamp, physical date, etc.')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    teacher_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_tickets'
    )

    class Meta:
        verbose_name = 'Assignment Ticket'
        verbose_name_plural = 'Assignment Tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id} - {self.student.user.get_full_name()} - {self.assignment.title}"


# =====================
# BRUSH-UP REQUEST MODEL
# =====================

class BrushUpRequest(models.Model):
    """Student requests for brush-up sessions or re-tests on failed tests."""

    REQUEST_TYPE_CHOICES = [
        ('brushup', 'Brush-Up Session'),
        ('retest', 'Re-test Request'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='brushup_requests')
    topic = models.ForeignKey(RoadmapTopic, on_delete=models.CASCADE, related_name='brushup_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_date = models.DateTimeField(null=True, blank=True)
    teacher_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Brush-Up Request'
        verbose_name_plural = 'Brush-Up Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_request_type_display()} - {self.topic.title}"


# =====================
# NOTIFICATION MODEL
# =====================

class Notification(models.Model):
    """In-app notifications for all user roles."""

    NOTIFICATION_TYPE_CHOICES = [
        ('assignment', 'New Assignment'),
        ('grade', 'Grade Posted'),
        ('comment', 'New Comment'),
        ('holiday', 'Holiday Announcement'),
        ('attendance', 'Attendance Alert'),
        ('general', 'General Notification'),
        ('ticket', 'Ticket Update'),
        ('brushup', 'Brush-Up Update'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"


# =====================
# FEEDBACK MODEL
# =====================

class Feedback(models.Model):
    """Parent/student feedback submitted to admin."""

    FEEDBACK_TYPE_CHOICES = [
        ('suggestion', 'Suggestion'),
        ('complaint', 'Complaint'),
        ('appreciation', 'Appreciation'),
        ('query', 'Query'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    response = models.TextField(blank=True)
    responded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='responded_feedback'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.submitted_by.get_full_name()} - {self.subject}"


# =====================
# ANNOUNCEMENT MODEL
# =====================

class Announcement(models.Model):
    """School-wide announcements with priority levels."""

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    TARGET_ROLE_CHOICES = [
        ('all', 'Everyone'),
        ('student', 'Students'),
        ('parent', 'Parents'),
        ('teacher', 'Teachers'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    target_audience = models.CharField(max_length=20, choices=TARGET_ROLE_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


# =====================
# SUBJECT MODEL
# =====================

class Subject(models.Model):
    """
    Subjects created by Admin and assigned to a Teacher.
    SerialNumber = auto PK (Django handles this automatically).
    TID = teacher ForeignKey (UserProfile where role='teacher').
    SET_NULL on teacher delete — subject is never lost, just unassigned
    until Admin reassigns it.
    """

    teacher = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects',
        limit_choices_to={'role': 'teacher'},
        help_text='Teacher responsible for this subject'
    )
    name = models.CharField(
        max_length=100,
        help_text='Subject name e.g. Mathematics, Science, ICT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['name']
        # Same subject name CAN exist under different teachers — valid per schema

    def __str__(self):
        if self.teacher and self.teacher.user:
            return f"{self.name} — {self.teacher.user.get_full_name()}"
        return f"{self.name} — Unassigned"


# =====================
# SUBJECTS TAKEN MODEL
# =====================

class SubjectsTaken(models.Model):
    """
    Join table: which subjects a student is enrolled in.
    student → Student (roll_number is unique on Student model).
    subject → Subject.
    unique_together prevents duplicate enrolments.
    CASCADE on both: deleting student or subject auto-cleans enrolments.
    """

    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='subjects_taken',
        help_text='Student enrolled in this subject'
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        related_name='enrolled_students',
        help_text='Subject the student is enrolled in'
    )
    enrolled_at = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Subject Taken'
        verbose_name_plural = 'Subjects Taken'
        ordering = ['student', 'subject__name']
        unique_together = ['student', 'subject']

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} "
            f"({self.student.roll_number}) → {self.subject.name}"
        )


# =====================
# TEACHER PROFILE MODEL
# =====================

class TeacherProfile(models.Model):
    """
    Teacher-specific data extending UserProfile.
    Created manually by Admin in /admin/ when a teacher is added.
    OneToOne with UserProfile (role='teacher').
    Salary is stored as Decimal for accurate financial calculations.
    """

    QUALIFICATION_CHOICES = [
        ('b_ed', 'B.Ed'),
        ('m_ed', 'M.Ed'),
        ('b_sc', 'B.Sc'),
        ('m_sc', 'M.Sc'),
        ('b_a', 'B.A'),
        ('m_a', 'M.A'),
        ('phd', 'Ph.D'),
        ('other', 'Other'),
    ]

    profile = models.OneToOneField(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        limit_choices_to={'role': 'teacher'},
        help_text='UserProfile of the teacher (role must be teacher)'
    )
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Monthly salary e.g. 12000.00'
    )
    joining_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date teacher joined the school'
    )
    qualification = models.CharField(
        max_length=10,
        choices=QUALIFICATION_CHOICES,
        blank=True,
        help_text='Highest academic qualification'
    )
    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        help_text='Emergency contact phone number'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'
        ordering = ['profile__user__first_name', 'profile__user__last_name']

    def __str__(self):
        return f"{self.profile.user.get_full_name()} — Teacher Profile"

    def get_full_name(self):
        return self.profile.user.get_full_name()

    def get_subjects(self):
        """Return all subjects assigned to this teacher."""
        return Subject.objects.filter(teacher=self.profile)

    def get_salary_display(self):
        """Return formatted salary string."""
        return f"₹{self.salary:,.2f}"
# =====================
# FEES STATUS MODEL
# =====================

class FeesStatus(models.Model):
    """
    Monthly fee record per student.
    Created by Admin — one record per student per month.
    PendingAmount on Parent is updated automatically via save().
    Student is flagged for discontinuation if 2+ months are Overdue.
    """

    STATUS_CHOICES = [
        ('unpaid',  'Unpaid'),
        ('paid',    'Paid'),
        ('overdue', 'Overdue'),
        ('waived',  'Waived'),
    ]

    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name='fees',
        help_text='Student this fee record belongs to'
    )
    month = models.CharField(
        max_length=7,
        help_text='Month and year in MM/YYYY format e.g. 01/2026'
    )
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Fee amount set by Admin e.g. 10000.00'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='unpaid',
        help_text='Payment status'
    )
    due_date = models.DateField(
        help_text='Date by which payment is due'
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date payment was received — leave blank if not yet paid'
    )
    remarks = models.TextField(
        blank=True,
        help_text='Optional notes e.g. partial payment, scholarship etc.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fee Status'
        verbose_name_plural = 'Fee Status Records'
        ordering = ['-month', 'student']
        unique_together = ['student', 'month']
        # Prevents duplicate fee records for same student same month

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} "
            f"({self.student.roll_number}) — "
            f"{self.month} — {self.get_status_display()}"
        )

    def save(self, *args, **kwargs):
        """
        Auto-update parent's PendingAmount when fee status changes.
        Also auto-set paid_date when status changes to paid.
        """
        from datetime import date as today_date

        # Auto-set paid_date when marked as paid
        if self.status == 'paid' and not self.paid_date:
            self.paid_date = today_date.today()

        # Clear paid_date if status changed away from paid
        if self.status != 'paid':
            self.paid_date = None

        super().save(*args, **kwargs)

        # Update parent's running PendingAmount
        self._update_parent_pending()

        # Check discontinuation flag (2+ overdue payments)
        self._check_discontinuation()

    def _update_parent_pending(self):
        """Recalculate and update parent's PendingAmount."""
        try:
            parent_user = self.student.parent
            if not parent_user:
                return

            # Sum all unpaid + overdue fees for this student
            from django.db.models import Sum
            total_pending = FeesStatus.objects.filter(
                student=self.student,
                status__in=['unpaid', 'overdue']
            ).aggregate(total=Sum('fees'))['total'] or 0

            # Update UserProfile of parent — store in a new field
            # (we add pending_amount to UserProfile in the next step)
            profile = parent_user.profile
            profile.pending_amount = total_pending
            profile.save(update_fields=['pending_amount'])
        except Exception:
            pass

    def _check_discontinuation(self):
        """Flag student if 2 or more payments are overdue."""
        try:
            overdue_count = FeesStatus.objects.filter(
                student=self.student,
                status='overdue'
            ).count()

            student = self.student
            if overdue_count >= 2:
                student.is_active = False
            else:
                student.is_active = True
            student.save(update_fields=['is_active'])
        except Exception:
            pass

    def is_overdue(self):
        """Returns True if unpaid and past due date."""
        from datetime import date as today_date
        return self.status == 'unpaid' and self.due_date < today_date.today()

# =====================
# TEACHER ATTENDANCE MODEL
# =====================

class TeacherAttendance(models.Model):
    """
    Teacher attendance — marked by Admin.
    Separate from student Attendance for clean querying,
    salary calculation, and permission separation.
    """

    STATUS_CHOICES = [
        ('present',  'Present'),
        ('absent',   'Absent'),
        ('late',     'Late'),
        ('excused',  'Excused'),
        ('half_day', 'Half Day'),
    ]

    teacher = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='teacher_attendance',
        limit_choices_to={'role': 'teacher'},
        help_text='Teacher whose attendance is being marked'
    )
    date = models.DateField(
        default=date.today,
        help_text='Date of attendance'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        help_text='Attendance status'
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='marked_teacher_attendance',
        help_text='Admin who marked this attendance'
    )
    notes = models.TextField(
        blank=True,
        help_text='Reason for absence or any relevant note'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Teacher Attendance'
        verbose_name_plural = 'Teacher Attendance Records'
        ordering = ['-date', 'teacher']
        unique_together = ['teacher', 'date']
        # Prevents duplicate attendance for same teacher same day

    def __str__(self):
        return (
            f"{self.teacher.user.get_full_name()} — "
            f"{self.date} — {self.get_status_display()}"
        )

    def get_attendance_rate(self):
        """Calculate attendance percentage for this teacher."""
        total = TeacherAttendance.objects.filter(teacher=self.teacher).count()
        if total == 0:
            return 0
        present = TeacherAttendance.objects.filter(
            teacher=self.teacher,
            status__in=['present', 'late', 'half_day']
        ).count()
        return round((present / total) * 100, 2)
    
# =====================
# PETTY CASH MODELS
# =====================
class PettyExpense(models.Model):
    CATEGORY_CHOICES = [
        ('rent',       'Rent'),
        ('stationary', 'Stationary'),
        ('events',     'Events'),
        ('utilities',  'Utilities'),
        ('other',      'Other'),
    ]
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    date        = models.DateField(default=date.today)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    added_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Petty Expense'

    def __str__(self):
        return f"{self.description} — ₹{self.amount} ({self.date})"

# =====================
# SIGNAL HANDLERS
# =====================

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when User is created."""
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'student'})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        try:
            instance.profile.save()
        except Exception:
            pass
