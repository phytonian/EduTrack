"""
EduTrack Django Admin Registration
====================================
This file registers all EduTrack models with Django's built-in admin panel at /admin/.
The admin panel is only accessible to superusers and staff users.
Each class below controls how a model appears and behaves inside the admin panel —
what columns show in the list, what filters are available, what fields appear on the
edit page, and what bulk actions are available.

Why this file matters:
- Admin is the fastest way for a developer/superuser to directly inspect and fix data.
- Custom list_display columns, search fields, and filters make it usable at a glance.
- Bulk actions (mark as paid, mark as absent, etc.) save time for common tasks.
"""

from django.contrib import admin
from .models import (
    UserProfile, Student, Assignment, Submission,
    RoadmapTopic, Attendance, TestScore, Comment,
    Holiday, StatusPost, AssignmentTicket, BrushUpRequest,
    Notification, Feedback, Announcement,
    Subject, SubjectsTaken, TeacherProfile, FeesStatus,
    TeacherAttendance, PettyExpense
)


# ─────────────────────────────────────────────────────────────
# USER PROFILE ADMIN
# Shows every user account's extended profile (role, phone, etc.)
# UserProfile is a OneToOne extension of Django's built-in User model.
# Use this to check a user's role (admin/teacher/student/parent)
# or to quickly find someone by name/username.
# ─────────────────────────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # Columns shown in the list view
    list_display = ['user', 'role', 'phone_number', 'created_at']

    # Sidebar filter — filter by role to quickly see all teachers, students, etc.
    list_filter = ['role']

    # Search box — search by username or full name
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


# ─────────────────────────────────────────────────────────────
# STUDENT ADMIN
# Shows student-specific data: roll number, grade, section, active status.
# A Student record is linked to a UserProfile with role='student'.
# Use this to check enrolment status, find a student by roll number,
# or manually activate/deactivate a student account.
# ─────────────────────────────────────────────────────────────
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Columns shown in the list view
    list_display = ['user', 'roll_number', 'grade', 'section', 'is_active']

    # Filter by grade, section, or active/inactive status
    list_filter = ['grade', 'section', 'is_active']

    # Search by student name or roll number
    search_fields = ['user__first_name', 'user__last_name', 'roll_number']

    # Clicking the user column takes you to the edit page
    list_display_links = ['user']


# ─────────────────────────────────────────────────────────────
# ASSIGNMENT ADMIN
# Shows all assignments created by teachers.
# Assignments are the core task unit — teachers create them,
# students submit work against them.
# Use this to inspect due dates, check which teacher created what,
# or manually change an assignment's status.
# ─────────────────────────────────────────────────────────────
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    # Show key details at a glance
    list_display = ['title', 'created_by', 'subject', 'grade', 'due_date', 'status']

    # Filter by status (active/draft/closed) or grade
    list_filter = ['status', 'grade']

    # Search by assignment title or subject name
    search_fields = ['title', 'subject']


# ─────────────────────────────────────────────────────────────
# SUBMISSION ADMIN
# Shows student submissions for assignments.
# A Submission is created when a student submits work for an Assignment.
# It holds the score, status (submitted/graded/late), and timestamp.
# Use this to find ungraded submissions or check a student's score.
# ─────────────────────────────────────────────────────────────
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'status', 'score', 'submitted_at']

    # Filter by status to find all ungraded or late submissions quickly
    list_filter = ['status']

    # Search by student name or assignment title
    search_fields = ['student__user__first_name', 'assignment__title']


# ─────────────────────────────────────────────────────────────
# ROADMAP TOPIC ADMIN
# Shows all roadmap topics (curriculum items) created by teachers.
# Topics form a tree — a topic can have a parent_topic (sub-topic).
# Each topic has a status: upcoming / in_progress / completed.
# Use this to inspect the curriculum structure or fix ordering.
# ─────────────────────────────────────────────────────────────
@admin.register(RoadmapTopic)
class RoadmapTopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'status', 'order', 'parent_topic']

    # Filter by status or by teacher to see a specific teacher's roadmap
    list_filter = ['status', 'created_by']

    # Search by topic title
    search_fields = ['title']


# ─────────────────────────────────────────────────────────────
# STUDENT ATTENDANCE ADMIN
# Shows student attendance records marked by teachers.
# Each record is one student on one date with a status and optional note.
# Use this to audit attendance data or fix incorrect records.
# ─────────────────────────────────────────────────────────────
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    # Show student, date, status, who marked it, and any note
    list_display = ['student', 'date', 'status', 'marked_by', 'notes']

    # Filter by status (present/absent/late) or by date
    list_filter = ['status', 'date']

    # Search by student name or roll number
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__roll_number',
    ]

    # Most recent records shown first
    ordering = ['-date']


# ─────────────────────────────────────────────────────────────
# TEST SCORE ADMIN
# Shows test/exam scores entered by teachers for students.
# Scores are linked to a RoadmapTopic so progress can be tracked.
# Use this to review scores, fix errors, or check pass/fail rates.
# ─────────────────────────────────────────────────────────────
@admin.register(TestScore)
class TestScoreAdmin(admin.ModelAdmin):
    list_display = ['student', 'test_name', 'subject', 'date', 'score', 'max_score']

    # Filter by subject to see all tests for a particular subject
    list_filter = ['subject']


# ─────────────────────────────────────────────────────────────
# COMMENT ADMIN
# Shows teacher/admin comments left on student profiles.
# Comments can be private (only visible to admin/teacher)
# or public (visible to parent too).
# Use this to audit communication or remove inappropriate comments.
# ─────────────────────────────────────────────────────────────
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'target_user', 'comment_type', 'is_private', 'created_at']

    # Filter by type (academic/behaviour/general) or private/public
    list_filter = ['comment_type', 'is_private']


# ─────────────────────────────────────────────────────────────
# HOLIDAY ADMIN
# Shows holidays and working day announcements created by admin.
# Each holiday has a type (Holiday/Working Day/Half Day) and
# can be marked as recurring annually.
# Use this to review the school calendar or fix dates.
# ─────────────────────────────────────────────────────────────
@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'holiday_type', 'is_recurring']

    # Filter by type to separate holidays from working days
    list_filter = ['holiday_type']


# ─────────────────────────────────────────────────────────────
# STATUS POST ADMIN
# Shows announcements/posts created by admin for specific roles.
# A post can target all users, or just students/parents/teachers.
# Pinned posts appear at the top of the feed.
# Use this to delete outdated posts or check what was broadcast.
# ─────────────────────────────────────────────────────────────
@admin.register(StatusPost)
class StatusPostAdmin(admin.ModelAdmin):
    list_display = ['author', 'target_role', 'is_pinned', 'created_at']


# ─────────────────────────────────────────────────────────────
# ASSIGNMENT TICKET ADMIN
# Shows tickets raised by students for offline submissions
# (email, WhatsApp, physical handover).
# Teachers respond to tickets and mark them verified/rejected.
# Use this to see all open tickets or manually update status.
# ─────────────────────────────────────────────────────────────
@admin.register(AssignmentTicket)
class AssignmentTicketAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'submission_method', 'status', 'created_at']

    # Filter by status (open/acknowledged/verified/rejected) or submission method
    list_filter = ['status', 'submission_method']


# ─────────────────────────────────────────────────────────────
# BRUSH-UP REQUEST ADMIN
# Shows student requests for brush-up sessions or re-tests
# on topics where they scored below the pass threshold.
# Teachers approve/schedule/reject these requests.
# Use this to see all pending requests or audit completed ones.
# ─────────────────────────────────────────────────────────────
@admin.register(BrushUpRequest)
class BrushUpRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'topic', 'request_type', 'status', 'created_at']

    # Filter by status or request type (brushup/retest)
    list_filter = ['status', 'request_type']


# ─────────────────────────────────────────────────────────────
# NOTIFICATION ADMIN
# Shows in-app notifications sent to any user.
# Notifications are auto-created by the system when events happen
# (new assignment, grade posted, holiday announced, etc.)
# Use this to check what notifications were sent or mark them read.
# ─────────────────────────────────────────────────────────────
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']

    # Filter by type or read/unread status
    list_filter = ['notification_type', 'is_read']


# ─────────────────────────────────────────────────────────────
# FEEDBACK ADMIN
# Shows feedback submitted by parents or students to admin.
# Feedback has types (academic/facility/teacher/general) and
# a status (pending/reviewed/resolved).
# Use this to review feedback and update resolution status.
# ─────────────────────────────────────────────────────────────
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['submitted_by', 'feedback_type', 'subject', 'status', 'created_at']

    # Filter by status or feedback type
    list_filter = ['status', 'feedback_type']


# ─────────────────────────────────────────────────────────────
# ANNOUNCEMENT ADMIN
# Shows school-wide announcements with priority levels.
# Announcements can target specific audiences and be activated/deactivated.
# Different from StatusPost — Announcements have priority and active flag.
# Use this to manage important school-wide messages.
# ─────────────────────────────────────────────────────────────
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'target_audience', 'is_active', 'created_at']

    # Filter by priority (high/medium/low), audience, or active status
    list_filter = ['priority', 'target_audience', 'is_active']


# ─────────────────────────────────────────────────────────────
# SUBJECT ADMIN
# Shows all subjects in the system, each assigned to a teacher.
# A Subject belongs to one teacher's UserProfile (role='teacher').
# Students enrol in subjects via SubjectsTaken (separate model).
# Use this to create subjects or reassign them to a different teacher.
# ─────────────────────────────────────────────────────────────
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    # Show subject name and teacher's full name (via custom method below)
    list_display = ['name', 'get_teacher_name', 'created_at']

    # Filter by teacher to see all subjects under a specific teacher
    list_filter = ['teacher']

    # Search by subject name or teacher name
    search_fields = ['name', 'teacher__user__first_name', 'teacher__user__last_name']

    ordering = ['name']

    def get_teacher_name(self, obj):
        """
        Returns the full name of the teacher assigned to this subject.
        Shows '— Unassigned —' if no teacher is linked.
        Used as a custom column in the list view since teacher is a FK,
        not a plain text field, so it can't be used in list_display directly.
        """
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name()
        return '— Unassigned —'
    get_teacher_name.short_description = 'Teacher'  # Column header label


# ─────────────────────────────────────────────────────────────
# SUBJECTS TAKEN ADMIN
# Shows which students are enrolled in which subjects.
# SubjectsTaken is a many-to-many bridge between Student and Subject
# with an enrolled_at timestamp. One record = one student in one subject.
# Use this to enrol/remove students from subjects or audit enrolments.
# ─────────────────────────────────────────────────────────────
@admin.register(SubjectsTaken)
class SubjectsTakenAdmin(admin.ModelAdmin):
    # Custom display columns (all via methods below since they cross FK relationships)
    list_display = ['get_student_name', 'get_roll_number', 'get_subject_name', 'get_teacher_name', 'enrolled_at']

    # Filter by subject or by the teacher assigned to the subject
    list_filter = ['subject', 'subject__teacher']

    # Search by student name, roll number, or subject name
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__roll_number',
        'subject__name',
    ]

    ordering = ['student__roll_number', 'subject__name']

    def get_student_name(self, obj):
        """Returns the enrolled student's full name."""
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student'

    def get_roll_number(self, obj):
        """Returns the enrolled student's roll number."""
        return obj.student.roll_number
    get_roll_number.short_description = 'Roll Number'

    def get_subject_name(self, obj):
        """Returns the subject name this enrolment is for."""
        return obj.subject.name
    get_subject_name.short_description = 'Subject'

    def get_teacher_name(self, obj):
        """
        Returns the full name of the teacher who owns the subject.
        Shows '— Unassigned —' if the subject has no teacher linked.
        """
        if obj.subject.teacher and obj.subject.teacher.user:
            return obj.subject.teacher.user.get_full_name()
        return '— Unassigned —'
    get_teacher_name.short_description = 'Teacher'


# ─────────────────────────────────────────────────────────────
# TEACHER PROFILE ADMIN
# Shows extended teacher data: salary, qualification, joining date.
# TeacherProfile is a OneToOne extension of UserProfile (role='teacher').
# Created by admin when a teacher account is set up.
# Use this to update salaries, check qualifications, or fix joining dates.
# ─────────────────────────────────────────────────────────────
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name',      # Teacher's full name (via method)
        'get_subjects',       # Comma-separated list of their subjects (via method)
        'get_salary_display', # Formatted salary like ₹12,000.00 (via method)
        'qualification',      # Highest degree (B.Ed, M.Sc, Ph.D etc.)
        'joining_date',       # Date they joined the school
        'emergency_contact',  # Emergency phone number
    ]

    # Filter by qualification or joining year
    list_filter = ['qualification', 'joining_date']

    # Search by teacher's name or email
    search_fields = [
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__user__email',
    ]

    ordering = ['profile__user__first_name']

    # fieldsets organises the edit page into named sections
    fieldsets = (
        ('Teacher', {
            'fields': ('profile',)                          # Link to the UserProfile
        }),
        ('Employment Details', {
            'fields': ('salary', 'joining_date', 'qualification')
        }),
        ('Contact', {
            'fields': ('emergency_contact',)
        }),
    )

    def get_full_name(self, obj):
        """Returns the teacher's full name from the linked User account."""
        return obj.profile.user.get_full_name()
    get_full_name.short_description = 'Teacher Name'

    def get_subjects(self, obj):
        """
        Returns a comma-separated list of all subjects assigned to this teacher.
        Calls the model's get_subjects() method which queries Subject.objects
        filtered by this teacher's profile.
        Shows '— No subjects assigned —' if none exist yet.
        """
        subjects = obj.get_subjects()
        if subjects.exists():
            return ', '.join(s.name for s in subjects)
        return '— No subjects assigned —'
    get_subjects.short_description = 'Subjects'

    def get_salary_display(self, obj):
        """
        Returns the formatted salary string (e.g. ₹12,000.00).
        Calls the model's get_salary_display() method.
        """
        return obj.get_salary_display()
    get_salary_display.short_description = 'Salary'


# ─────────────────────────────────────────────────────────────
# FEES STATUS ADMIN
# Shows monthly fee records for each student.
# One FeesStatus record = one student for one month (e.g. 02/2026).
# Status can be: Unpaid / Paid / Overdue / Waived.
# When status changes, the parent's pending_amount auto-updates via model's save().
# 2+ overdue records automatically sets the student as inactive.
# Use this to create fee records, mark payments, or investigate overdue cases.
# ─────────────────────────────────────────────────────────────
@admin.register(FeesStatus)
class FeesStatusAdmin(admin.ModelAdmin):
    list_display = [
        'get_student_name',  # Student's full name (via method)
        'get_roll_number',   # Roll number (via method)
        'month',             # Month in MM/YYYY format
        'fees',              # Fee amount
        'status',            # Unpaid/Paid/Overdue/Waived
        'due_date',          # Date payment was due
        'paid_date',         # Date payment was received (auto-set when marked Paid)
    ]

    # Filter by payment status or month
    list_filter = ['status', 'month']

    # Search by student name, roll number, or month string
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__roll_number',
        'month',
    ]

    # Most recent months first
    ordering = ['-month', 'student__roll_number']

    # created_at and updated_at are auto-set — show but don't allow editing
    readonly_fields = ['created_at', 'updated_at']

    # Organise the edit page into named sections
    fieldsets = (
        ('Student', {
            'fields': ('student',)
        }),
        ('Fee Details', {
            'fields': ('month', 'fees', 'status', 'due_date', 'paid_date')
        }),
        ('Notes', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Hidden by default, click to expand
        }),
    )

    def get_student_name(self, obj):
        """Returns the student's full name from the linked User account."""
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student'

    def get_roll_number(self, obj):
        """Returns the student's roll number."""
        return obj.student.roll_number
    get_roll_number.short_description = 'Roll Number'

    # ── Bulk actions ──────────────────────────────────────────
    # These appear in the "Action" dropdown in the list view.
    # Select multiple records, choose an action, click Go.
    actions = ['mark_as_paid', 'mark_as_overdue', 'mark_as_waived']

    def mark_as_paid(self, request, queryset):
        """
        Bulk action: marks all selected fee records as Paid.
        Calls .save() on each record individually so the model's
        save() logic runs — this auto-sets paid_date and
        recalculates the parent's pending_amount.
        """
        for fee in queryset:
            fee.status = 'paid'
            fee.save()
        self.message_user(request, f'{queryset.count()} fee(s) marked as Paid.')
    mark_as_paid.short_description = 'Mark selected as Paid'

    def mark_as_overdue(self, request, queryset):
        """
        Bulk action: marks all selected fee records as Overdue.
        Calls .save() individually so auto-logic runs (clears paid_date,
        recalculates pending, checks if student should be deactivated).
        """
        for fee in queryset:
            fee.status = 'overdue'
            fee.save()
        self.message_user(request, f'{queryset.count()} fee(s) marked as Overdue.')
    mark_as_overdue.short_description = 'Mark selected as Overdue'

    def mark_as_waived(self, request, queryset):
        """
        Bulk action: marks all selected fee records as Waived (fee forgiven).
        Calls .save() individually so pending_amount recalculates correctly.
        """
        for fee in queryset:
            fee.status = 'waived'
            fee.save()
        self.message_user(request, f'{queryset.count()} fee(s) marked as Waived.')
    mark_as_waived.short_description = 'Mark selected as Waived'


# ─────────────────────────────────────────────────────────────
# PETTY EXPENSE ADMIN
# Shows small operational expenses logged by admin:
# rent, stationary, events, utilities, etc.
# These are used in the Finance Overview page to calculate
# total expenses and net balance (income minus expenses).
# Use this to add, edit, or delete expense records.
# ─────────────────────────────────────────────────────────────
@admin.register(PettyExpense)
class PettyExpenseAdmin(admin.ModelAdmin):
    # Show description, amount, category, date, and who added it
    list_display = ['description', 'amount', 'category', 'date', 'added_by']

    # Filter by category or date to find specific expense types
    list_filter = ['category', 'date']


# ─────────────────────────────────────────────────────────────
# TEACHER ATTENDANCE ADMIN
# Shows attendance records for teachers, marked by admin.
# Separate from student Attendance for clean querying and
# salary calculation purposes (absent days can affect salary).
# Each record is one teacher on one date — unique_together prevents duplicates.
# Use this to view attendance history, fix incorrect records,
# or bulk-mark teachers for a given day.
# ─────────────────────────────────────────────────────────────
@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'get_teacher_name',  # Teacher's full name (via method)
        'date',              # Date of attendance
        'status',            # Present/Absent/Late/Half Day/Excused
        'marked_by',         # Admin who marked this record
        'notes',             # Optional reason or note
    ]

    # Filter by status, date, or teacher
    list_filter = ['status', 'date', 'teacher']

    # Search by teacher first or last name
    search_fields = [
        'teacher__user__first_name',
        'teacher__user__last_name',
    ]

    # Most recent dates first
    ordering = ['-date']

    # created_at is auto-set — show but don't allow editing
    readonly_fields = ['created_at']

    # Organise the edit page into named sections
    fieldsets = (
        ('Teacher', {
            'fields': ('teacher', 'date')
        }),
        ('Attendance', {
            'fields': ('status', 'marked_by', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)  # Hidden by default
        }),
    )

    def get_teacher_name(self, obj):
        """Returns the teacher's full name from their linked User account."""
        return obj.teacher.user.get_full_name()
    get_teacher_name.short_description = 'Teacher'

    # ── Bulk actions ──────────────────────────────────────────
    # Select multiple attendance records and apply status in one click.
    # Note: these use queryset.update() for speed (no model save() logic needed
    # for attendance — unlike FeesStatus which has side effects in save()).
    actions = ['mark_present', 'mark_absent', 'mark_half_day']

    def mark_present(self, request, queryset):
        """Bulk action: marks all selected records as Present."""
        queryset.update(status='present')
        self.message_user(request, f'{queryset.count()} record(s) marked as Present.')
    mark_present.short_description = 'Mark selected as Present'

    def mark_absent(self, request, queryset):
        """Bulk action: marks all selected records as Absent."""
        queryset.update(status='absent')
        self.message_user(request, f'{queryset.count()} record(s) marked as Absent.')
    mark_absent.short_description = 'Mark selected as Absent'

    def mark_half_day(self, request, queryset):
        """Bulk action: marks all selected records as Half Day."""
        queryset.update(status='half_day')
        self.message_user(request, f'{queryset.count()} record(s) marked as Half Day.')
    mark_half_day.short_description = 'Mark selected as Half Day'
