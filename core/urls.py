"""
EduTrack Core URL Configuration
All routes for all roles: admin, teacher, parent, student.
"""

from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    # Auth
    LoginView, LogoutView, DashboardView,

    # Admin
    AdminDashboardView, AdminStudentListView, StudentCreateView,
    StudentUpdateView, StudentDeleteView, StudentDetailView, StudentGridView,
    ParentCreateView, ParentListView, ParentUpdateView, ParentDeleteView,
    TeacherListView, TeacherCreateView, TeacherUpdateView, TeacherDeleteView,
    AllTeachersRoadmapView, HolidayBroadcastView, HolidayListView, HolidayDeleteView,
    StatusPostCreateView, StatusPostListView, StatusPostDeleteView,
    AdminAnalyticsView,AdminNotificationListView,AdminMarkNotificationReadView,
    AdminMarkAllNotificationsReadView,AdminTicketListView,AdminBrushUpListView,AdminAssignmentListView,
    AdminTeacherAttendanceView, AdminFinanceView, AdminTeacherPerformanceView,PettyExpense,

    # Teacher
    TeacherDashboardView, StudentListView, TeacherStudentDetailView,
    AssignmentListView, AssignmentCreateView, AssignmentUpdateView,
    AssignmentDeleteView, AssignmentDetailView,
    SubmissionListView, SubmissionDetailView, SubmissionGradeView, GradeSubmissionView,
    RoadmapTopicListView, RoadmapTopicCreateView, RoadmapTopicUpdateView,
    RoadmapTopicDeleteView, RoadmapTreeView, RoadmapCSVUploadView,
    download_roadmap_template,
    AttendanceMarkView, AttendanceHistoryView, BulkAttendanceView,
    TicketListViewTeacher, TicketResponseView,
    BrushUpRequestListViewTeacher, BrushUpResponseView,

    # Parent
    ParentDashboardView, ParentStudentProgressView, ParentAssignmentStatusView,
    ParentRoadmapView, ParentFeedbackView, ParentStudentAttendanceView, ParentAttendanceView,

    # Student
    StudentDashboardView, StudentAssignmentListView, StudentAssignmentDetailView,
    StudentSubmissionCreateView, StudentProgressView, StudentRoadmapView,
    StudentAttendanceView, StudentTestScoresView,
    RaiseTicketView, TicketListView, TicketDetailView,
    BrushUpRequestView, BrushUpRequestListView, RetestRequestView,

    # Common
    ProfilePhotoUpdateView, ProfileUpdateView, ProfileDetailView,
    CommentCreateView, CommentListView, CommentDeleteView,
    NotificationListView, MarkNotificationReadView, MarkAllNotificationsReadView,

    # API
    RoadmapTreeAPIView, AssignmentStatusAPIView, StudentProgressAPIView,
    AttendanceAPIView, NotificationCountAPIView,
)

# NOTE: No app_name here — all views use plain URL names (no namespace)

urlpatterns = [

    # =====================
    # AUTH
    # =====================
    path('', LoginView.as_view(), name='login'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Password Change
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html',
        success_url='/password-change/done/'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'), name='password_change_done'),

    # =====================
    # ADMIN PANEL
    # =====================
    path('admin-panel/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-panel/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),

    path('admin-panel/students/', AdminStudentListView.as_view(), name='admin_student_list'),
    path('admin-panel/students/grid/', StudentGridView.as_view(), name='student_grid'),
    path('admin-panel/student/add/', StudentCreateView.as_view(), name='student_add'),
    path('admin-panel/student/<int:pk>/', StudentDetailView.as_view(), name='student_detail'),
    path('admin-panel/student/<int:pk>/edit/', StudentUpdateView.as_view(), name='student_edit'),
    path('admin-panel/student/<int:pk>/delete/', StudentDeleteView.as_view(), name='student_delete'),

    path('admin-panel/parents/', ParentListView.as_view(), name='parent_list'),
    path('admin-panel/parent/add/', ParentCreateView.as_view(), name='parent_add'),
    path('admin-panel/parent/<int:pk>/edit/', ParentUpdateView.as_view(), name='parent_edit'),
    path('admin-panel/parent/<int:pk>/delete/', ParentDeleteView.as_view(), name='parent_delete'),

    path('admin-panel/teachers/', TeacherListView.as_view(), name='teacher_list'),
    path('admin-panel/teacher/add/', TeacherCreateView.as_view(), name='teacher_add'),
    path('admin-panel/teacher/<int:pk>/edit/', TeacherUpdateView.as_view(), name='teacher_edit'),
    path('admin-panel/teacher/<int:pk>/delete/', TeacherDeleteView.as_view(), name='teacher_delete'),

    path('admin-panel/roadmaps/', AllTeachersRoadmapView.as_view(), name='all_roadmaps'),

    path('admin-panel/holidays/', HolidayListView.as_view(), name='holiday_list'),
    path('admin-panel/holiday/add/', HolidayBroadcastView.as_view(), name='holiday_add'),
    path('admin-panel/holiday/<int:pk>/delete/', HolidayDeleteView.as_view(), name='holiday_delete'),

    path('admin-panel/status/post/', StatusPostCreateView.as_view(), name='status_post'),
    path('admin-panel/status/list/', StatusPostListView.as_view(), name='status_list'),
    path('admin-panel/status/<int:pk>/delete/', StatusPostDeleteView.as_view(), name='status_delete'),
    path('admin-panel/notifications/', AdminNotificationListView.as_view(), name='admin_notifications'),
    path('admin-panel/notification/<int:pk>/read/', AdminMarkNotificationReadView.as_view(), name='admin_mark_notification_read'),
    path('admin-panel/notifications/read-all/', AdminMarkAllNotificationsReadView.as_view(), name='admin_mark_all_notifications_read'),
    path('admin-panel/tickets/', AdminTicketListView.as_view(), name='admin_tickets'),
    path('admin-panel/brushups/', AdminBrushUpListView.as_view(), name='admin_brushups'),
    path('admin-panel/assignments/', AdminAssignmentListView.as_view(), name='admin_assignment_list'),
    path('admin-panel/teacher-attendance/', AdminTeacherAttendanceView.as_view(), name='admin_teacher_attendance'),
    path('admin-panel/finance/', AdminFinanceView.as_view(), name='admin_finance'),
    path('admin-panel/teacher-performance/', AdminTeacherPerformanceView.as_view(), name='admin_teacher_performance'),

    # =====================
    # TEACHER
    # =====================
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),

    path('teacher/students/', StudentListView.as_view(), name='student_list'),
    path('teacher/student/<int:pk>/', TeacherStudentDetailView.as_view(), name='teacher_student_detail'),

    path('teacher/assignments/', AssignmentListView.as_view(), name='assignment_list'),
    path('teacher/assignment/create/', AssignmentCreateView.as_view(), name='assignment_create'),
    path('teacher/assignment/<int:pk>/', AssignmentDetailView.as_view(), name='assignment_detail'),
    path('teacher/assignment/<int:pk>/edit/', AssignmentUpdateView.as_view(), name='assignment_edit'),
    path('teacher/assignment/<int:pk>/delete/', AssignmentDeleteView.as_view(), name='assignment_delete'),

    path('teacher/assignment/<int:assignment_id>/submissions/', SubmissionListView.as_view(), name='submission_list'),
    path('teacher/submission/<int:pk>/', SubmissionDetailView.as_view(), name='submission_detail'),
    path('teacher/submission/<int:pk>/grade/', SubmissionGradeView.as_view(), name='submission_grade'),
    path('teacher/submission/<int:pk>/grade-quick/', GradeSubmissionView.as_view(), name='grade_submission'),

    path('teacher/roadmap/', RoadmapTopicListView.as_view(), name='roadmap_list'),
    path('teacher/roadmap/create/', RoadmapTopicCreateView.as_view(), name='roadmap_create'),
    path('teacher/roadmap/<int:pk>/edit/', RoadmapTopicUpdateView.as_view(), name='roadmap_edit'),
    path('teacher/roadmap/<int:pk>/delete/', RoadmapTopicDeleteView.as_view(), name='roadmap_delete'),
    path('teacher/roadmap/tree/', RoadmapTreeView.as_view(), name='roadmap_tree'),
    path('teacher/roadmap/upload/', RoadmapCSVUploadView.as_view(), name='roadmap_upload'),
    path('teacher/roadmap/template/', download_roadmap_template, name='download_roadmap_template'),

    path('teacher/attendance/', AttendanceMarkView.as_view(), name='mark_attendance'),
    path('teacher/attendance/bulk/', BulkAttendanceView.as_view(), name='bulk_attendance'),
    path('teacher/attendance/history/', AttendanceHistoryView.as_view(), name='attendance_history'),
    path('teacher/attendance/student/<int:student_id>/', AttendanceHistoryView.as_view(), name='student_attendance_history'),

    path('teacher/tickets/', TicketListViewTeacher.as_view(), name='teacher_tickets'),
    path('teacher/ticket/<int:pk>/respond/', TicketResponseView.as_view(), name='ticket_respond'),

    path('teacher/brushup-requests/', BrushUpRequestListViewTeacher.as_view(), name='teacher_brushup_requests'),
    path('teacher/brushup/<int:pk>/respond/', BrushUpResponseView.as_view(), name='brushup_respond'),
    path('teacher/assignment/add/', AssignmentCreateView.as_view(), name='assignment_add'),

    # =====================
    # PARENT
    # =====================
    path('parent/dashboard/', ParentDashboardView.as_view(), name='parent_dashboard'),
    path('parent/student/<int:student_id>/progress/', ParentStudentProgressView.as_view(), name='parent_student_progress'),
    path('parent/student/<int:student_id>/assignments/', ParentAssignmentStatusView.as_view(), name='parent_assignment_status'),
    path('parent/student/<int:student_id>/roadmap/', ParentRoadmapView.as_view(), name='parent_roadmap'),
    path('parent/student/<int:student_id>/attendance/', ParentStudentAttendanceView.as_view(), name='parent_student_attendance'),
    path('parent/attendance/<int:student_id>/', ParentAttendanceView.as_view(), name='parent_attendance'),
    path('parent/feedback/', ParentFeedbackView.as_view(), name='parent_feedback'),

    # =====================
    # STUDENT
    # =====================
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/assignments/', StudentAssignmentListView.as_view(), name='student_assignments'),
    path('student/assignment/<int:pk>/', StudentAssignmentDetailView.as_view(), name='student_assignment_detail'),
    path('student/assignment/<int:assignment_id>/submit/', StudentSubmissionCreateView.as_view(), name='student_submit_assignment'),
    path('student/progress/', StudentProgressView.as_view(), name='student_progress'),
    path('student/roadmap/', StudentRoadmapView.as_view(), name='student_roadmap'),
    path('student/attendance/', StudentAttendanceView.as_view(), name='student_attendance'),
    path('student/attendance/<int:pk>/', StudentAttendanceView.as_view(), name='student_attendance_detail'),
    path('student/test-scores/', StudentTestScoresView.as_view(), name='student_test_scores'),
    path('student/ticket/raise/', RaiseTicketView.as_view(), name='raise_ticket'),
    path('student/tickets/', TicketListView.as_view(), name='ticket_list'),
    path('student/ticket/<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('student/brushup/request/', BrushUpRequestView.as_view(), name='brushup_request'),
    path('student/brushup/list/', BrushUpRequestListView.as_view(), name='brushup_list'),
    path('student/retest/request/<int:test_id>/', RetestRequestView.as_view(), name='retest_request'),

    # =====================
    # COMMON (All Roles)
    # =====================
    path('profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/photo/update/', ProfilePhotoUpdateView.as_view(), name='profile_photo_update'),

    path('comment/add/<int:user_id>/', CommentCreateView.as_view(), name='comment_add'),
    path('comments/<int:user_id>/', CommentListView.as_view(), name='comment_list'),
    path('comment/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment_delete'),

    path('roadmaps/', AllTeachersRoadmapView.as_view(), name='public_roadmaps'),
    path('roadmap/tree/', RoadmapTreeView.as_view(), name='roadmap_tree_public'),

    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notification/<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/read-all/', MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),

    # =====================
    # API ENDPOINTS
    # =====================
    path('api/roadmap/tree/', RoadmapTreeAPIView.as_view(), name='api_roadmap_tree'),
    path('api/roadmap/tree/<int:teacher_id>/', RoadmapTreeAPIView.as_view(), name='api_teacher_roadmap_tree'),
    path('api/assignment/<int:assignment_id>/status/', AssignmentStatusAPIView.as_view(), name='api_assignment_status'),
    path('api/student/<int:student_id>/progress/', StudentProgressAPIView.as_view(), name='api_student_progress'),
    path('api/attendance/<int:student_id>/', AttendanceAPIView.as_view(), name='api_attendance'),
    path('api/notifications/count/', NotificationCountAPIView.as_view(), name='api_notification_count'),
]
