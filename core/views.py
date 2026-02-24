"""
EduTrack Core Views
Fixed: Adding student/parent (page hanging), clicking student on dashboard,
       assignment creation, comments, submission status, roadmap tree view.
New:   Photo update for all roles, profile update, roadmap tree badges,
       admin analytics, all-teachers roadmap view, holiday broadcast.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.db.models import Avg, Sum, Count, Q
from django.db.models.functions import TruncMonth
from datetime import date, datetime, timedelta
import csv
import json

from .models import (
    Student, Assignment, Submission, RoadmapTopic, UserProfile,
    TestScore, Comment, StatusPost, Holiday, Attendance,
    AssignmentTicket, BrushUpRequest, Feedback, Notification,
    TeacherAttendance, TeacherProfile, FeesStatus, PettyExpense, Subject,
)
from .forms import (
    StudentForm, AssignmentForm, SubmissionForm, RoadmapTopicForm,
    FeedbackForm, ParentForm, TeacherForm, CommentForm, ProfilePhotoForm,
    ProfileUpdateForm, UserNameForm, AttendanceForm, StatusPostForm,
    HolidayForm, GradeSubmissionForm, AssignmentTicketForm,
    BrushUpRequestForm, BrushUpResponseForm, TicketResponseForm
)

# ============================================================================
# ROLE-BASED ACCESS MIXINS
# ============================================================================

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_superuser or
            (hasattr(self.request.user, 'profile') and
             self.request.user.profile.role == 'admin')
        )

    def handle_no_permission(self):
        messages.error(self.request, 'Admin access required.')
        return redirect('dashboard')
#---------------------------------------------------------------------------------------------------

class TeacherOrAdminMixin(UserPassesTestMixin):
    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        return self.request.user.profile.role in ('teacher', 'admin') or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'Teacher or Admin access required.')
        return redirect('dashboard')
#---------------------------------------------------------------------------------------------------

class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            hasattr(self.request.user, 'profile') and
            self.request.user.profile.is_teacher()
        )

    def handle_no_permission(self):
        messages.error(self.request, 'Teacher access only.')
        return redirect('dashboard')
#---------------------------------------------------------------------------------------------------

class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            hasattr(self.request.user, 'profile') and
            self.request.user.profile.is_student()
        )

    def handle_no_permission(self):
        messages.error(self.request, 'Student access only.')
        return redirect('dashboard')
#---------------------------------------------------------------------------------------------------

class ParentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            hasattr(self.request.user, 'profile') and
            self.request.user.profile.is_parent()
        )

    def handle_no_permission(self):
        messages.error(self.request, 'Parent access only.')
        return redirect('dashboard')


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class LoginView(View):
    """Login with profile photo support — works for all roles."""
    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, self.template_name)
#---------------------------------------------------------------------------------------------------

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('login')
#---------------------------------------------------------------------------------------------------

class DashboardView(LoginRequiredMixin, View):
    """Redirects to role-specific dashboard. FIXED: handles missing UserProfile."""
    def get(self, request):
        # Auto-create profile if missing (e.g. superuser created via createsuperuser)
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'role': 'admin' if request.user.is_superuser else 'student'}
        )
        role = profile.role
        if role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'student':
            return redirect('student_dashboard')
        elif role == 'parent':
            return redirect('parent_dashboard')
        messages.error(request, 'Your account has no role. Contact admin.')
        return redirect('login')


# ============================================================================
# COMMON VIEWS — All Roles
# ============================================================================

class ProfilePhotoUpdateView(LoginRequiredMixin, View):
    """All roles can update their profile photo."""
    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile photo updated!')
        else:
            messages.error(request, 'Error updating photo. Use JPG/PNG/GIF.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
#---------------------------------------------------------------------------------------------------

class ProfileDetailView(LoginRequiredMixin, View):
    """View own profile."""
    template_name = 'profile/profile_detail.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {'profile': profile})
#---------------------------------------------------------------------------------------------------

class ProfileUpdateView(LoginRequiredMixin, View):
    """Update profile info and name."""
    template_name = 'profile/profile_update.html'

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
        name_form = UserNameForm(instance=request.user)
        return render(request, self.template_name, {
            'profile_form': profile_form,
            'name_form': name_form
        })

    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        name_form = UserNameForm(request.POST, instance=request.user)
        if profile_form.is_valid() and name_form.is_valid():
            profile_form.save()
            name_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_detail')
        return render(request, self.template_name, {
            'profile_form': profile_form,
            'name_form': name_form
        })
#---------------------------------------------------------------------------------------------------

class CommentCreateView(LoginRequiredMixin, View):
    """Admin or teacher posts a comment on any user's profile."""
    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.target_user = target_user
            comment.save()
            messages.success(request, 'Comment posted.')
        else:
            messages.error(request, 'Error posting comment.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
#---------------------------------------------------------------------------------------------------
    
class CommentListView(LoginRequiredMixin, ListView):
    model = Comment
    template_name = 'comments/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 20

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        qs = Comment.objects.filter(target_user_id=user_id)
        # Non-admins cannot see private comments
        if not (self.request.user.is_superuser or
                (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')):
            qs = qs.filter(is_private=False)
        return qs
#---------------------------------------------------------------------------------------------------

class CommentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        if comment.author == request.user or request.user.is_superuser:
            comment.delete()
            messages.success(request, 'Comment deleted.')
        else:
            messages.error(request, 'Permission denied.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
#---------------------------------------------------------------------------------------------------

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
#---------------------------------------------------------------------------------------------------

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({'status': 'ok'})
#---------------------------------------------------------------------------------------------------

class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')


# ============================================================================
# ADMIN VIEWS
# ============================================================================

class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/dashboard.html'

    def get(self, request):
        context = {
            'total_students': Student.objects.count(),
            'total_teachers': User.objects.filter(profile__role='teacher').count(),
            'total_parents': User.objects.filter(profile__role='parent').count(),
            'total_assignments': Assignment.objects.count(),
            'active_assignments': Assignment.objects.filter(status='active').count(),
            'recent_students': Student.objects.select_related('user').order_by('-id')[:5],
            'recent_assignments': Assignment.objects.order_by('-created_at')[:5],
            'upcoming_holidays': Holiday.objects.filter(date__gte=date.today()).order_by('date')[:5],
            'status_posts': StatusPost.objects.order_by('-is_pinned', '-created_at')[:5],
            'pending_tickets': AssignmentTicket.objects.filter(status='open').count(),
            'pending_brushup': BrushUpRequest.objects.filter(status='pending').count(),
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class AdminNotificationListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/notification_list.html'
    paginate_by = 30

    def get(self, request):
        role_filter = request.GET.get('role', '')

        all_qs = Notification.objects.select_related('user', 'user__profile').order_by('-created_at')
        unread_qs = all_qs.filter(is_read=False)

        if role_filter:
            all_qs = all_qs.filter(user__profile__role=role_filter)
            unread_qs = unread_qs.filter(user__profile__role=role_filter)

        from django.core.paginator import Paginator
        paginator = Paginator(all_qs, self.paginate_by)
        page = request.GET.get('page', 1)
        all_notifications = paginator.get_page(page)

        context = {
            'unread_notifications': unread_qs[:50],
            'all_notifications':    all_notifications,
            'unread_count':         unread_qs.count(),
            'total_count':          Notification.objects.count(),
            'open_tickets':         AssignmentTicket.objects.filter(status='open').count(),
            'pending_brushups':     BrushUpRequest.objects.filter(status='pending').count(),
            'role_filter':          role_filter,
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class AdminMarkNotificationReadView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk)
        notif.is_read = True
        notif.save()
        return redirect('admin_notifications')


class AdminMarkAllNotificationsReadView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('admin_notifications')
#---------------------------------------------------------------------------------------------------

class AdminTicketListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/ticket_list.html'

    def get(self, request):
        status_filter = request.GET.get('status', '')
        tickets = AssignmentTicket.objects.select_related(
            'student__user', 'assignment', 'resolved_by'
        ).order_by('-created_at')

        if status_filter:
            tickets = tickets.filter(status=status_filter)

        context = {
            'tickets':        tickets,
            'status_filter':  status_filter,
            'all_count':      AssignmentTicket.objects.count(),
            'open_count':     AssignmentTicket.objects.filter(status='open').count(),
            'ack_count':      AssignmentTicket.objects.filter(status='acknowledged').count(),
            'verified_count': AssignmentTicket.objects.filter(status='verified').count(),
            'rejected_count': AssignmentTicket.objects.filter(status='rejected').count(),
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class AdminBrushUpListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/brushup_list.html'

    def get(self, request):
        status_filter = request.GET.get('status', '')
        brushups = BrushUpRequest.objects.select_related(
            'student__user', 'topic'
        ).order_by('-created_at')

        if status_filter:
            brushups = brushups.filter(status=status_filter)

        context = {
            'brushups':        brushups,
            'status_filter':   status_filter,
            'all_count':       BrushUpRequest.objects.count(),
            'pending_count':   BrushUpRequest.objects.filter(status='pending').count(),
            'approved_count':  BrushUpRequest.objects.filter(status='approved').count(),
            'scheduled_count': BrushUpRequest.objects.filter(status='scheduled').count(),
            'completed_count': BrushUpRequest.objects.filter(status='completed').count(),
            'rejected_count':  BrushUpRequest.objects.filter(status='rejected').count(),
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class StudentDetailView(LoginRequiredMixin, View):
    """
    FIXED: Clicking student on dashboard now leads to this detailed student page.
    Available to admin AND teacher (TeacherOrAdminMixin).
    """
    template_name = 'admin/student_detail.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        submissions = Submission.objects.filter(student=student).select_related('assignment')
        test_scores = TestScore.objects.filter(student=student).order_by('-date')

        total_assignments = submissions.count()
        completed = submissions.filter(status='graded').count()
        pending = submissions.filter(status='submitted').count()
        avg_score = submissions.filter(
            status='graded', score__isnull=False
        ).aggregate(Avg('score'))['score__avg'] or 0

        attendance_records = Attendance.objects.filter(student=student)
        total_days = attendance_records.count()
        present_days = attendance_records.filter(status='present').count()
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0

        comments = Comment.objects.filter(target_user=student.user).order_by('-created_at')

        roadmap_topics = RoadmapTopic.objects.all()
        completed_topics = roadmap_topics.filter(status='completed').count()
        total_topics = roadmap_topics.count()
        roadmap_progress = (completed_topics / total_topics * 100) if total_topics > 0 else 0

        comment_form = CommentForm()

        context = {
            'student': student,
            'total_assignments': total_assignments,
            'completed_assignments': completed,
            'pending_assignments': pending,
            'average_score': round(avg_score, 2),
            'attendance_rate': round(attendance_rate, 2),
            'recent_scores': test_scores[:5],
            'recent_submissions': submissions.order_by('-submitted_at')[:5],
            'comments': comments,
            'comment_form': comment_form,
            'roadmap_progress': round(roadmap_progress, 2),
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class StudentGridView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Complex grid/list reporting system for admin."""
    template_name = 'admin/student_grid.html'

    def get(self, request):
        students = Student.objects.all().select_related('user', 'user__profile')
        grades = sorted(Student.objects.values_list('grade', flat=True).distinct())

        # Filter by grade if requested
        grade_filter = request.GET.get('grade', '')
        section_filter = request.GET.get('section', '')
        search = request.GET.get('search', '')

        if grade_filter:
            students = students.filter(grade=grade_filter)
        if section_filter:
            students = students.filter(section=section_filter)
        if search:
            students = students.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(roll_number__icontains=search)
            )

        students_data = []
        for student in students:
            submissions = Submission.objects.filter(student=student)
            att = Attendance.objects.filter(student=student)
            total_att = att.count()
            present = att.filter(status='present').count()
            avg_score = submissions.filter(
                status='graded', score__isnull=False
            ).aggregate(Avg('score'))['score__avg'] or 0

            students_data.append({
                'student': student,
                'attendance_rate': round((present / total_att * 100), 1) if total_att > 0 else 0,
                'average_score': round(avg_score, 2),
                'total_assignments': submissions.count(),
                'graded': submissions.filter(status='graded').count(),
                'pending': submissions.filter(status='submitted').count(),
            })

        context = {
            'students_data': students_data,
            'grades': grades,
            'grade_filter': grade_filter,
            'section_filter': section_filter,
            'search': search,
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class AdminStudentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Student
    template_name = 'admin/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        return Student.objects.select_related('user', 'parent').all()
#---------------------------------------------------------------------------------------------------

class StudentCreateView(LoginRequiredMixin, TeacherOrAdminMixin, View):
    """
    FIXED: Student creation — uses plain Form.save() in atomic transaction.
    No more hanging page.
    """
    template_name = 'admin/student_form.html'

    def get(self, request):
        rolls = Student.objects.values_list('roll_number', flat=True)
        numeric_rolls = []
        for r in rolls:
            r_stripped = r.lstrip('S').lstrip('s')
            if r_stripped.isdigit():
                numeric_rolls.append(int(r_stripped))
        next_num = max(numeric_rolls) + 1 if numeric_rolls else 1
        next_roll = f'S{str(next_num).zfill(3)}'
        form = StudentForm(initial={'roll_number': next_roll})
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                student = form.save()
                messages.success(request, f'Student {student.user.get_full_name()} added successfully!')
                return redirect('admin_student_list')
            except Exception as e:
                messages.error(request, f'Error creating student: {str(e)}')
        return render(request, self.template_name, {'form': form})
#---------------------------------------------------------------------------------------------------

class StudentUpdateView(LoginRequiredMixin, TeacherOrAdminMixin, View):
    template_name = 'admin/student_edit.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        from core.models import Subject, SubjectsTaken
        all_subjects = Subject.objects.select_related('teacher').order_by('name')
        enrolled_ids = set(
            SubjectsTaken.objects.filter(student=student).values_list('subject_id', flat=True)
        )
        return render(request, self.template_name, {
            'object': student,
            'all_subjects': all_subjects,
            'enrolled_ids': enrolled_ids,
            'SECTION_CHOICES': [('A','A'),('B','B'),('C','C'),('D','D')],
            'BLOOD_GROUP_CHOICES': [
                ('','—'),('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
            ],
            'parents': User.objects.filter(profile__role='parent').order_by('first_name'),
        })

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        from core.models import Subject, SubjectsTaken

        # Update basic fields
        student.grade    = request.POST.get('grade', student.grade)
        student.section  = request.POST.get('section', student.section)
        student.phone_number = request.POST.get('phone_number', student.phone_number)
        student.address  = request.POST.get('address', student.address)
        student.blood_group = request.POST.get('blood_group', student.blood_group)
        student.medical_conditions = request.POST.get('medical_conditions', student.medical_conditions)
        student.is_active = request.POST.get('is_active') == 'on'

        parent_id = request.POST.get('parent')
        if parent_id:
            try:
                student.parent = User.objects.get(pk=parent_id)
            except User.DoesNotExist:
                pass
        else:
            student.parent = None

        student.save()

        # Update subject enrolments
        selected_subject_ids = set(
            int(x) for x in request.POST.getlist('subjects') if x.isdigit()
        )
        current_subject_ids = set(
            SubjectsTaken.objects.filter(student=student).values_list('subject_id', flat=True)
        )

        # Add new enrolments
        to_add = selected_subject_ids - current_subject_ids
        SubjectsTaken.objects.bulk_create([
            SubjectsTaken(student=student, subject_id=sid) for sid in to_add
        ], ignore_conflicts=True)

        # Remove removed enrolments
        to_remove = current_subject_ids - selected_subject_ids
        SubjectsTaken.objects.filter(student=student, subject_id__in=to_remove).delete()

        messages.success(request, f'Student {student.user.get_full_name()} updated successfully!')
        return redirect('admin_student_list')
    
#---------------------------------------------------------------------------------------------------

class StudentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Student
    template_name = 'admin/student_confirm_delete.html'
    success_url = reverse_lazy('admin_student_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Student deleted.')
        return super().delete(request, *args, **kwargs)
#---------------------------------------------------------------------------------------------------

class AdminAssignmentListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/assignment_list.html'

    def get(self, request):
        from django.core.paginator import Paginator
        status_filter = request.GET.get('status', 'active')  # default to active

        assignments = Assignment.objects.select_related(
            'created_by'
        ).prefetch_related('submissions').order_by('-created_at')

        if status_filter:
            assignments = assignments.filter(status=status_filter)

        paginator = Paginator(assignments, 20)
        page = request.GET.get('page', 1)
        assignments = paginator.get_page(page)

        context = {
            'assignments':   assignments,
            'status_filter': status_filter,
            'all_count':     Assignment.objects.count(),
            'active_count':  Assignment.objects.filter(status='active').count(),
            'draft_count':   Assignment.objects.filter(status='draft').count(),
            'closed_count':  Assignment.objects.filter(status='closed').count(),
        }
        return render(request, self.template_name, context)

class AdminTeacherAttendanceView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/teacher_attendance.html'

    def get(self, request):
        from datetime import date as dt
        teachers = UserProfile.objects.filter(role='teacher').select_related('user')
        teacher_filter = request.GET.get('teacher_filter', '')
        month_filter   = request.GET.get('month_filter', dt.today().strftime('%Y-%m'))

        records = TeacherAttendance.objects.select_related(
            'teacher__user', 'marked_by'
        ).order_by('-date')

        if teacher_filter:
            records = records.filter(teacher__pk=teacher_filter)

        if month_filter:
            year, month = month_filter.split('-')
            records = records.filter(date__year=year, date__month=month)

        # Attendance rate per teacher (all time)
        teacher_stats = []
        for tp in teachers:
            all_rec  = TeacherAttendance.objects.filter(teacher=tp)
            total    = all_rec.count()
            present  = all_rec.filter(status__in=['present', 'late', 'half_day']).count()
            rate     = round(present / total * 100, 1) if total else 0
            teacher_stats.append({'name': tp.user.get_full_name(), 'present': present,
                                   'total': total, 'rate': rate})

        return render(request, self.template_name, {
            'teachers':       teachers,
            'records':        records,
            'teacher_stats':  teacher_stats,
            'teacher_filter': teacher_filter,
            'month_filter':   month_filter,
            'today':          dt.today().strftime('%Y-%m-%d'),
        })

    def post(self, request):
        from datetime import date as dt
        action = request.POST.get('action')
        date_str = request.POST.get('date', dt.today().strftime('%Y-%m-%d'))

        if action == 'single':
            teacher_id = request.POST.get('teacher_id')
            status     = request.POST.get('status')
            notes      = request.POST.get('notes', '')
            try:
                teacher = UserProfile.objects.get(pk=teacher_id, role='teacher')
                TeacherAttendance.objects.update_or_create(
                    teacher=teacher,
                    date=date_str,
                    defaults={'status': status, 'notes': notes, 'marked_by': request.user}
                )
                messages.success(request, f'Attendance marked for {teacher.user.get_full_name()}.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'Teacher not found.')

        elif action == 'bulk':
            teachers = UserProfile.objects.filter(role='teacher')
            count = 0
            for teacher in teachers:
                status = request.POST.get(f'status_{teacher.pk}')
                if status:
                    TeacherAttendance.objects.update_or_create(
                        teacher=teacher,
                        date=date_str,
                        defaults={'status': status, 'notes': '', 'marked_by': request.user}
                    )
                    count += 1
            messages.success(request, f'Bulk attendance marked for {count} teachers.')

        return redirect('admin_teacher_attendance')


class AdminFinanceView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/finance.html'

    def get(self, request):
        from datetime import date as dt
        from django.db.models import Sum
        selected_month = request.GET.get('month', dt.today().strftime('%Y-%m'))
        year, month    = selected_month.split('-')
        month_str      = f"{month}/{year}"  # MM/YYYY format used in FeesStatus

        # Fee income for selected month
        fee_records  = FeesStatus.objects.filter(month=month_str).select_related('student__user')
        paid_fees    = fee_records.filter(status='paid')
        pending_fees = fee_records.filter(status__in=['unpaid', 'overdue'])
        total_income  = paid_fees.aggregate(t=Sum('fees'))['t'] or 0
        total_pending = pending_fees.aggregate(t=Sum('fees'))['t'] or 0

        # Salary expenses (all teachers + admin)
        salary_records = []
        total_salary   = 0
        for tp in TeacherProfile.objects.select_related('profile__user'):
            salary_records.append({
                'name':   tp.profile.user.get_full_name(),
                'role':   'Teacher',
                'salary': tp.salary,
            })
            total_salary += float(tp.salary)

        # Petty expenses for selected month
        petty_expenses = PettyExpense.objects.filter(
            date__year=year, date__month=month
        )
        total_petty = petty_expenses.aggregate(t=Sum('amount'))['t'] or 0

        total_expenses = total_salary + float(total_petty)
        net_balance    = float(total_income) - total_expenses

        return render(request, self.template_name, {
            'selected_month':    selected_month,
            'fee_records':       fee_records,
            'paid_fees_count':   paid_fees.count(),
            'pending_fees_count':pending_fees.count(),
            'total_income':      total_income,
            'total_pending':     total_pending,
            'salary_records':    salary_records,
            'total_salary':      total_salary,
            'petty_expenses':    petty_expenses,
            'total_petty':       total_petty,
            'total_expenses':    total_expenses,
            'net_balance':       net_balance,
            'today':             dt.today().strftime('%Y-%m-%d'),
        })

    def post(self, request):
        action = request.POST.get('action')
        if action == 'add_expense':
            PettyExpense.objects.create(
                description  = request.POST.get('description'),
                amount       = request.POST.get('amount'),
                date         = request.POST.get('expense_date'),
                added_by     = request.user,
            )
            messages.success(request, 'Petty expense added.')
        elif action == 'delete_expense':
            PettyExpense.objects.filter(pk=request.POST.get('expense_id')).delete()
            messages.success(request, 'Expense deleted.')
        return redirect('admin_finance')


class AdminTeacherPerformanceView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/teacher_performance.html'

    def get(self, request):
        from django.db.models import Avg
        teachers = User.objects.filter(profile__role='teacher').select_related('profile')
        teacher_data = []

        for teacher in teachers:
            assignments   = Assignment.objects.filter(created_by=teacher)
            all_subs      = Submission.objects.filter(assignment__in=assignments)
            graded_subs   = all_subs.filter(status='graded', score__isnull=False)
            pending_subs  = all_subs.filter(status='submitted')
            topics        = RoadmapTopic.objects.filter(created_by=teacher)
            completed     = topics.filter(status='completed')
            tests_sched   = topics.filter(test_scheduled__isnull=False).count()
            avg_score_val = graded_subs.aggregate(a=Avg('score'))['a'] or 0
            roadmap_pct   = round(completed.count() / topics.count() * 100, 1) if topics.count() else 0
            grading_rate  = round(graded_subs.count() / all_subs.count() * 100, 1) if all_subs.count() else 0

            # Average grading time (submitted_at → updated_at for graded)
            avg_grading_days = 0
            graded_with_dates = graded_subs.exclude(submitted_at=None)
            if graded_with_dates.exists():
                total_days = sum(
                    (s.updated_at.date() - s.submitted_at.date()).days
                    for s in graded_with_dates
                    if s.updated_at and s.submitted_at
                )
                avg_grading_days = round(total_days / graded_with_dates.count(), 1)

            # Student progress cards
            student_scores = []
            seen = set()
            for sub in graded_subs.select_related('student__user').order_by('-score'):
                sid = sub.student.pk
                if sid not in seen:
                    seen.add(sid)
                    pct = round(float(sub.score) / float(sub.assignment.max_score) * 100, 1) \
                          if sub.assignment.max_score else 0
                    student_scores.append({'name': sub.student.user.get_full_name(), 'score': pct})

            # Subjects
            subjects = list(
                Subject.objects.filter(teacher=teacher.profile).values_list('name', flat=True)
            )

            # Qualification
            qualification = ''
            try:
                qualification = teacher.profile.teacher_profile.get_qualification_display()
            except Exception:
                pass

            # Overall performance score (weighted)
            overall = round(
                (grading_rate * 0.3) + (roadmap_pct * 0.3) + (float(avg_score_val) * 0.4), 1
            )

            teacher_data.append({
                'teacher':          teacher,
                'subjects':         subjects,
                'qualification':    qualification,
                'total_assignments':assignments.count(),
                'graded_count':     graded_subs.count(),
                'pending_count':    pending_subs.count(),
                'avg_grading_days': avg_grading_days,
                'total_topics':     topics.count(),
                'completed_topics': completed.count(),
                'tests_scheduled':  tests_sched,
                'avg_student_score':round(float(avg_score_val), 1),
                'grading_rate':     grading_rate,
                'roadmap_pct':      roadmap_pct,
                'students':         student_scores,
                'overall_score':    overall,
            })

        # Sort by overall score descending
        teacher_data.sort(key=lambda x: x['overall_score'], reverse=True)

        return render(request, self.template_name, {'teacher_data': teacher_data})

    
#===================================================================================================
# --- Parent Management ---
#===================================================================================================

class ParentCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """FIXED: Parent creation — atomic, no hanging."""
    template_name = 'admin/parent_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ParentForm()})

    def post(self, request):
        form = ParentForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Parent {user.get_full_name()} added successfully!')
                return redirect('parent_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return render(request, self.template_name, {'form': form})
#---------------------------------------------------------------------------------------------------

class ParentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin/parent_list.html'
    context_object_name = 'parents'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.filter(profile__role='parent').select_related('profile')
#---------------------------------------------------------------------------------------------------

class ParentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'admin/parent_edit.html'
    success_url = reverse_lazy('parent_list')

    def form_valid(self, form):
        messages.success(self.request, 'Parent updated!')
        return super().form_valid(form)
#---------------------------------------------------------------------------------------------------

class ParentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'admin/parent_confirm_delete.html'
    success_url = reverse_lazy('parent_list')

    def get_queryset(self):
        return User.objects.filter(profile__role='parent')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Parent deleted.')
        return super().delete(request, *args, **kwargs)

#=======================================
# --- Teacher Management ---
#=======================================

class TeacherListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.filter(profile__role='teacher').select_related('profile')
#---------------------------------------------------------------------------------------------------

class TeacherCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/teacher_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': TeacherForm()})

    def post(self, request):
        form = TeacherForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Teacher {user.get_full_name()} added!')
                return redirect('teacher_list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        return render(request, self.template_name, {'form': form})

#---------------------------------------------------------------------------------------------------
class TeacherUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'admin/teacher_edit.html'
    success_url = reverse_lazy('teacher_list')

    def get_queryset(self):
        return User.objects.filter(profile__role='teacher')

    def form_valid(self, form):
        messages.success(self.request, 'Teacher updated!')
        return super().form_valid(form)
#---------------------------------------------------------------------------------------------------

class TeacherDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'admin/teacher_confirm_delete.html'
    success_url = reverse_lazy('teacher_list')

    def get_queryset(self):
        return User.objects.filter(profile__role='teacher')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Teacher deleted.')
        return super().delete(request, *args, **kwargs)
#---------------------------------------------------------------------------------------------------

# --- Status / Holiday / Analytics ---

class StatusPostCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/status_post_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': StatusPostForm()})

    def post(self, request):
        form = StatusPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Status posted!')
        else:
            messages.error(request, 'Error posting status.')
        return redirect('admin_dashboard')
#---------------------------------------------------------------------------------------------------

class StatusPostListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = StatusPost
    template_name = 'admin/status_list.html'
    context_object_name = 'status_posts'
    paginate_by = 20
#---------------------------------------------------------------------------------------------------

class StatusPostDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(StatusPost, pk=pk)
        post.delete()
        messages.success(request, 'Post deleted.')
        return redirect('status_list')
#---------------------------------------------------------------------------------------------------

class HolidayBroadcastView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/holiday_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': HolidayForm()})

    def post(self, request):
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.created_by = request.user
            holiday.save()
            # Create notifications for ALL users
            all_users = User.objects.filter(is_active=True)
            notifications = [
                Notification(
                    user=u,
                    notification_type='holiday',
                    title=f'Holiday: {holiday.title}',
                    message=f'{holiday.title} on {holiday.date}. {holiday.description}',
                )
                for u in all_users
            ]
            Notification.objects.bulk_create(notifications)
            messages.success(request, f'Holiday "{holiday.title}" broadcast to all users!')
            return redirect('holiday_list')
        return render(request, self.template_name, {'form': form})
#---------------------------------------------------------------------------------------------------

class HolidayListView(LoginRequiredMixin, ListView):
    model = Holiday
    template_name = 'admin/holiday_list.html'
    context_object_name = 'holidays'

    def get_queryset(self):
        return Holiday.objects.all().order_by('date')
#---------------------------------------------------------------------------------------------------

class HolidayDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        holiday = get_object_or_404(Holiday, pk=pk)
        holiday.delete()
        messages.success(request, 'Holiday deleted.')
        return redirect('holiday_list')
#---------------------------------------------------------------------------------------------------

class AllTeachersRoadmapView(LoginRequiredMixin, View):
    """
    All roles can view all teachers' roadmaps.
    Admin can edit; others view only.
    """
    template_name = 'admin/all_roadmaps.html'

    def get(self, request):
        teachers = User.objects.filter(profile__role='teacher').select_related('profile')
        roadmaps_data = []
        for teacher in teachers:
            topics = RoadmapTopic.objects.filter(created_by=teacher)
            root_topics = topics.filter(parent_topic__isnull=True).order_by('order')
            roadmaps_data.append({
                'teacher': teacher,
                'total_topics': topics.count(),
                'completed_topics': topics.filter(status='completed').count(),
                'in_progress_topics': topics.filter(status='in_progress').count(),
                'upcoming_topics': topics.filter(status='upcoming').count(),
                'root_topics': root_topics[:5],
            })
        return render(request, self.template_name, {'roadmaps_data': roadmaps_data})
#---------------------------------------------------------------------------------------------------

class AdminAnalyticsView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admin/analytics.html'

    def get(self, request):
        students = Student.objects.all()
        submissions = Submission.objects.filter(status='graded', score__isnull=False)
        avg_score = submissions.aggregate(Avg('score'))['score__avg'] or 0

        # ── Grade-wise breakdown ─────────────────────────────────────────
        grade_stats = []
        for grade in sorted(Student.objects.values_list('grade', flat=True).distinct()):
            grade_students = students.filter(grade=grade)
            grade_submissions = Submission.objects.filter(
                student__in=grade_students, status='graded', score__isnull=False
            )
            grade_stats.append({
                'grade': grade,
                'student_count': grade_students.count(),
                'avg_score': round(
                    grade_submissions.aggregate(Avg('score'))['score__avg'] or 0, 1
                ),
            })

        # ── Per-student stats (for student performance list) ─────────────
        student_stats = []
        for student in students.select_related('user', 'user__profile'):
            subs = Submission.objects.filter(student=student)
            att  = Attendance.objects.filter(student=student)
            total_att = att.count()
            present   = att.filter(status='present').count()
            graded    = subs.filter(status='graded', score__isnull=False)
            avg       = graded.aggregate(Avg('score'))['score__avg'] or 0

            # pending fees from parent profile
            pending_fees = 0
            if student.parent:
                try:
                    pending_fees = student.parent.profile.pending_amount or 0
                except Exception:
                    pending_fees = 0

            student_stats.append({
                'student':       student,
                'avg_score':     round(avg, 1),
                'attendance_rate': round(present / total_att * 100, 1) if total_att else 0,
                'total':         subs.count(),
                'graded':        graded.count(),
                'pending_fees':  pending_fees,
            })

        # Sort by avg_score descending
        student_stats.sort(key=lambda x: x['avg_score'], reverse=True)

        # ── Per-teacher stats ────────────────────────────────────────────
        teachers = User.objects.filter(profile__role='teacher').select_related('profile')
        teacher_stats = []
        teacher_stats_json = []

        for teacher in teachers:
            t_assignments = Assignment.objects.filter(created_by=teacher)
            t_submissions = Submission.objects.filter(assignment__in=t_assignments)
            graded_subs   = t_submissions.filter(status='graded', score__isnull=False)
            pending_subs  = t_submissions.filter(status='submitted')
            t_avg         = graded_subs.aggregate(Avg('score'))['score__avg'] or 0

            # Roadmap progress
            roadmap_topics    = RoadmapTopic.objects.filter(created_by=teacher)
            total_topics      = roadmap_topics.count()
            completed_topics  = roadmap_topics.filter(status='completed').count()
            roadmap_pct       = round(completed_topics / total_topics * 100, 1) if total_topics else 0

            # Individual student scores under this teacher
            student_scores = []
            for sub in graded_subs.select_related('student__user')[:8]:
                student_scores.append({
                    'name':  sub.student.user.get_full_name(),
                    'score': round(sub.score, 1),
                })

            teacher_stats.append({
                'teacher':            teacher,
                'total_assignments':  t_assignments.count(),
                'graded_submissions': graded_subs.count(),
                'pending_submissions':pending_subs.count(),
                'avg_student_score':  round(t_avg, 1),
                'roadmap_progress':   roadmap_pct,
                'student_scores':     student_scores,
            })

            teacher_stats_json.append({
                'name':             teacher.get_full_name(),
                'avg_student_score':round(t_avg, 1),
                'graded':           graded_subs.count(),
                'pending':          pending_subs.count(),
            })

        # ── Monthly trend ────────────────────────────────────────────────
        monthly_data = list(
            Submission.objects.filter(status='graded')
            .annotate(month=TruncMonth('submitted_at'))
            .values('month')
            .annotate(count=Count('id'), avg=Avg('score'))
            .order_by('month')
        )

        context = {
            'total_students':    students.count(),
            'average_score':     round(avg_score, 1),
            'grade_stats':       grade_stats,
            'grade_stats_json':  json.dumps(grade_stats, default=lambda o: float(o) if hasattr(o, '__float__') else str(o)),
            'student_stats':     student_stats,
            'teacher_stats':     teacher_stats,
            'teacher_stats_json':json.dumps(teacher_stats_json, default=lambda o: float(o) if hasattr(o, '__float__') else str(o)),
            'monthly_data':      json.dumps(monthly_data, default=str),
            'open_tickets':      AssignmentTicket.objects.filter(status='open').count(),
            'pending_brushup':   BrushUpRequest.objects.filter(status='pending').count(),
        }
        return render(request, self.template_name, context)
    
# ============================================================================
# TEACHER VIEWS
# ============================================================================

class TeacherDashboardView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/dashboard.html'

    def get(self, request):
        teacher_assignments = Assignment.objects.filter(created_by=request.user)
        recent_submissions = Submission.objects.filter(
            assignment__created_by=request.user,
            status='submitted'
        ).select_related('student__user', 'assignment').order_by('-submitted_at')[:10]

        # Roadmap topics with tree for badge display
        roadmap_topics = RoadmapTopic.objects.filter(
            created_by=request.user, parent_topic__isnull=True
        ).prefetch_related('subtopics').order_by('order')

        context = {
            'total_students': Student.objects.count(),
            'total_assignments': teacher_assignments.count(),
            'active_assignments': teacher_assignments.filter(status='active').count(),
            'pending_reviews': Submission.objects.filter(
                assignment__created_by=request.user,
                status='submitted',
                score__isnull=True
            ).count(),
            'recent_submissions': recent_submissions,
            'upcoming_deadlines': teacher_assignments.filter(
                status='active', due_date__gte=date.today()
            ).order_by('due_date')[:5],
            'roadmap_topics': roadmap_topics,
            'roadmap_count': RoadmapTopic.objects.filter(created_by=request.user).count(),
            'open_tickets': AssignmentTicket.objects.filter(
                assignment__created_by=request.user, status='open'
            ).count(),
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

class StudentListView(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    """Teacher list of all students — clicking goes to student detail."""
    model = Student
    template_name = 'teacher/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        qs = Student.objects.all().select_related('user', 'parent')
        search = self.request.GET.get('search', '')
        grade = self.request.GET.get('grade', '')
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(roll_number__icontains=search)
            )
        if grade:
            qs = qs.filter(grade=grade)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['grades'] = sorted(Student.objects.values_list('grade', flat=True).distinct())
        return ctx
#---------------------------------------------------------------------------------------------------

class TeacherStudentDetailView(LoginRequiredMixin, TeacherRequiredMixin, View):
    """FIXED: Teacher clicks student → goes to this detail page."""
    template_name = 'teacher/student_detail.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        submissions = Submission.objects.filter(student=student).select_related('assignment')
        attendance = Attendance.objects.filter(student=student).order_by('-date')
        test_scores = TestScore.objects.filter(student=student).order_by('-date')
        comments = Comment.objects.filter(target_user=student.user)
        comment_form = CommentForm()

        total = attendance.count()
        present = attendance.filter(status='present').count()
        att_rate = round((present / total * 100), 1) if total > 0 else 0

        context = {
            'student': student,
            'submissions': submissions.order_by('-submitted_at')[:10],
            'attendance': attendance[:10],
            'attendance_rate': att_rate,
            'test_scores': test_scores[:10],
            'comments': comments,
            'comment_form': comment_form,
            'avg_score': round(
                submissions.filter(status='graded', score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0, 2
            ),
        }
        return render(request, self.template_name, context)
#---------------------------------------------------------------------------------------------------

# --- Assignment Management ---

class AssignmentListView(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    model = Assignment
    template_name = 'teacher/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        return Assignment.objects.filter(created_by=self.request.user).order_by('-created_at')


class AssignmentDetailView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/assignment_detail.html'

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
        submissions = Submission.objects.filter(assignment=assignment).select_related('student__user')
        stats = assignment.get_submission_stats()
        return render(request, self.template_name, {
            'assignment': assignment,
            'submissions': submissions,
            'stats': stats,
        })


class AssignmentCreateView(LoginRequiredMixin, TeacherRequiredMixin, View):
    """
    FIXED: Assignment creation — plain View to avoid ModelForm CSRF + file upload issues.
    Surfaces form errors clearly instead of silently swallowing them.
    """
    template_name = 'teacher/assignment_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': AssignmentForm(), 'action': 'Create'})

    def post(self, request):
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            # Auto-create submission records for all students
            students = Student.objects.all()
            Submission.objects.bulk_create([
                Submission(assignment=assignment, student=s, status='not_submitted')
                for s in students
                if not Submission.objects.filter(assignment=assignment, student=s).exists()
            ])
            messages.success(request, f'Assignment "{assignment.title}" created!')
            return redirect('assignment_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class AssignmentUpdateView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/assignment_form.html'

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
        form = AssignmentForm(instance=assignment)
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'assignment': assignment})

    def post(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated!')
            return redirect('assignment_list')
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'assignment': assignment})


class AssignmentDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = Assignment
    template_name = 'teacher/assignment_confirm_delete.html'
    success_url = reverse_lazy('assignment_list')

    def get_queryset(self):
        return Assignment.objects.filter(created_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment deleted.')
        return super().delete(request, *args, **kwargs)

#---------------------------------------------------------------------------------------------------
    
# --- Submission Management ---

class SubmissionListView(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    """Shows submission STATUS for each student — teacher dashboard."""
    model = Submission
    template_name = 'teacher/submission_list.html'
    context_object_name = 'submissions'
    paginate_by = 20

    def get_queryset(self):
        return Submission.objects.filter(
            assignment_id=self.kwargs['assignment_id']
        ).select_related('student', 'student__user').order_by('status', 'student__roll_number')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assignment'] = get_object_or_404(Assignment, pk=self.kwargs['assignment_id'])
        return ctx


class SubmissionDetailView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/submission_detail.html'

    def get(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)
        form = GradeSubmissionForm(initial={
            'score': submission.score,
            'feedback': submission.feedback,
            'status': submission.status if submission.status in ('graded', 'resubmit') else 'graded',
        })
        return render(request, self.template_name, {'submission': submission, 'form': form})


class SubmissionGradeView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/grade_submission.html'

    def get(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)
        form = GradeSubmissionForm()
        return render(request, self.template_name, {'submission': submission, 'form': form})

    def post(self, request, pk):
        submission = get_object_or_404(Submission, pk=pk)
        form = GradeSubmissionForm(request.POST)
        if form.is_valid():
            score = form.cleaned_data['score']
            if score > submission.assignment.max_score:
                messages.error(request, f'Score cannot exceed {submission.assignment.max_score}')
                return render(request, self.template_name, {'submission': submission, 'form': form})
            submission.score = score
            submission.feedback = form.cleaned_data['feedback']
            submission.status = form.cleaned_data['status']
            submission.graded_at = timezone.now()
            submission.graded_by = request.user
            submission.save()
            messages.success(request, 'Submission graded!')
            return redirect('submission_list', assignment_id=submission.assignment.id)
        return render(request, self.template_name, {'submission': submission, 'form': form})

#---------------------------------------------------------------------------------------------------
# Alias for URL compatibility
GradeSubmissionView = SubmissionGradeView
#---------------------------------------------------------------------------------------------------

# --- Roadmap Management ---

class RoadmapTopicListView(LoginRequiredMixin, TeacherRequiredMixin, View):
    """
    UPDATED: Topics displayed in hierarchy tree with badges.
    """
    template_name = 'teacher/roadmap_list.html'

    def get(self, request):
        # Only root topics, subtopics loaded via tree
        root_topics = RoadmapTopic.objects.filter(
            created_by=request.user, parent_topic__isnull=True
        ).prefetch_related('subtopics__subtopics').order_by('order')

        total = RoadmapTopic.objects.filter(created_by=request.user).count()
        completed = RoadmapTopic.objects.filter(created_by=request.user, status='completed').count()

        return render(request, self.template_name, {
            'root_topics': root_topics,
            'total': total,
            'completed': completed,
        })
#---------------------------------------------------------------------------------------------------

class RoadmapTopicCreateView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/roadmap_form.html'

    def get(self, request):
        form = RoadmapTopicForm(user=request.user)
        return render(request, self.template_name, {'form': form, 'action': 'Create'})

    def post(self, request):
        form = RoadmapTopicForm(request.POST, user=request.user)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.created_by = request.user
            topic.save()
            messages.success(request, f'Topic "{topic.title}" created!')
            return redirect('roadmap_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})
#---------------------------------------------------------------------------------------------------

class RoadmapTopicUpdateView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/roadmap_form.html'

    def get(self, request, pk):
        topic = get_object_or_404(RoadmapTopic, pk=pk, created_by=request.user)
        form = RoadmapTopicForm(instance=topic, user=request.user)
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'topic': topic})

    def post(self, request, pk):
        topic = get_object_or_404(RoadmapTopic, pk=pk, created_by=request.user)
        form = RoadmapTopicForm(request.POST, instance=topic, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Topic updated!')
            return redirect('roadmap_list')
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'topic': topic})
#---------------------------------------------------------------------------------------------------

class RoadmapTopicDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = RoadmapTopic
    template_name = 'teacher/roadmap_confirm_delete.html'
    success_url = reverse_lazy('roadmap_list')

    def get_queryset(self):
        return RoadmapTopic.objects.filter(created_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Topic deleted.')
        return super().delete(request, *args, **kwargs)
#---------------------------------------------------------------------------------------------------

class RoadmapTreeView(LoginRequiredMixin, View):
    """Tree view of teacher's roadmap with badges."""
    template_name = 'teacher/roadmap_tree.html'

    def get(self, request):
        # Show own roadmap for teachers, pick teacher_id for admin
        teacher_id = request.GET.get('teacher_id')
        if teacher_id and (request.user.is_superuser or
                           (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            owner = get_object_or_404(User, pk=teacher_id)
        else:
            owner = request.user

        topics = RoadmapTopic.objects.filter(created_by=owner).order_by('order')
        tree_data = _build_topic_tree(topics)

        return render(request, self.template_name, {
            'tree_data': json.dumps(tree_data),
            'total_topics': topics.count(),
            'completed': topics.filter(status='completed').count(),
            'owner': owner,
        })
#---------------------------------------------------------------------------------------------------

class RoadmapCSVUploadView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/roadmap_csv_upload.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('roadmap_list')

        try:
            decoded = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)
            created = 0
            errors = []

            for i, row in enumerate(reader, start=2):
                try:
                    parent_id = row.get('parent_id', '').strip()
                    parent_topic = None
                    if parent_id:
                        try:
                            parent_topic = RoadmapTopic.objects.get(id=int(parent_id))
                        except (RoadmapTopic.DoesNotExist, ValueError):
                            errors.append(f'Row {i}: Parent topic {parent_id} not found')
                            continue

                    RoadmapTopic.objects.create(
                        title=row['title'].strip(),
                        description=row.get('description', '').strip(),
                        order=int(row.get('order', 0) or 0),
                        status=row.get('status', 'upcoming').strip(),
                        parent_topic=parent_topic,
                        created_by=request.user,
                        subject=row.get('subject', '').strip(),
                        grade=row.get('grade', '').strip(),
                    )
                    created += 1
                except Exception as e:
                    errors.append(f'Row {i}: {str(e)}')

            if created:
                messages.success(request, f'{created} topics imported!')
            for err in errors[:5]:
                messages.warning(request, err)
            if len(errors) > 5:
                messages.warning(request, f'...and {len(errors) - 5} more errors.')

        except Exception as e:
            messages.error(request, f'CSV error: {str(e)}')

        return redirect('roadmap_list')
    
#---------------------------------------------------------------------------------------------------

def download_roadmap_template(request):
    """Download CSV template for roadmap upload."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="roadmap_template.csv"'
    writer = csv.writer(response)
    writer.writerow(['title', 'description', 'order', 'status', 'parent_id', 'subject', 'grade'])
    writer.writerow(['Introduction to Python', 'Basic syntax', '1', 'completed', '', 'CS', '10'])
    writer.writerow(['Variables', 'Data types', '2', 'in_progress', '1', 'CS', '10'])
    writer.writerow(['Control Flow', 'Loops and conditionals', '3', 'upcoming', '1', 'CS', '10'])
    return response
#---------------------------------------------------------------------------------------------------

# --- Attendance ---


class AttendanceMarkView(LoginRequiredMixin, TeacherRequiredMixin, View):
    """Teacher marks student attendance from dashboard with date selector."""
    template_name = 'teacher/attendance_form.html'

    def get(self, request):
        selected_date = request.GET.get('date', str(date.today()))
        try:
            att_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            att_date = date.today()

        students = Student.objects.filter(is_active=True).select_related('user').order_by('grade', 'section', 'roll_number')

        # Build a map of grade → list of unique subjects (from assignments)
        from .models import Assignment
        grade_subjects_map = {}
        for assignment in Assignment.objects.values('grade', 'subject').distinct():
            g = assignment['grade']
            s = assignment['subject']
            if g not in grade_subjects_map:
                grade_subjects_map[g] = []
            if s and s not in grade_subjects_map[g]:
                grade_subjects_map[g].append(s)

        # Attach subjects to each student object for template access
        for student in students:
            student.grade_subjects = grade_subjects_map.get(student.grade, [])

        existing = {
            a.student_id: a
            for a in Attendance.objects.filter(date=att_date)
        }

        return render(request, self.template_name, {
            'students': students,
            'att_date': att_date,
            'existing': existing,
        })

    def post(self, request):
        att_date_str = request.POST.get('date', str(date.today()))
        try:
            att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date()
        except ValueError:
            att_date = date.today()

        marked = 0
        for key, value in request.POST.items():
            if key.startswith('status_') and value:
                student_id = key.replace('status_', '')
                try:
                    student = Student.objects.get(id=student_id)
                    Attendance.objects.update_or_create(
                        student=student,
                        date=att_date,
                        defaults={
                            'status': value,
                            'marked_by': request.user,
                            'notes': request.POST.get(f'notes_{student_id}', ''),
                        }
                    )
                    marked += 1
                except Student.DoesNotExist:
                    continue

        messages.success(request, f'Attendance marked for {marked} students on {att_date}!')
        return redirect('mark_attendance')   # Stay on attendance page, not dashboard
#---------------------------------------------------------------------------------------------------

class AttendanceHistoryView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/attendance_report.html'

    def get(self, request, student_id=None):
        start = request.GET.get('start_date')
        end = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date() if start else date.today() - timedelta(days=30)
            end_date = datetime.strptime(end, '%Y-%m-%d').date() if end else date.today()
        except ValueError:
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()

        students = Student.objects.filter(id=student_id) if student_id else Student.objects.all()
        data = []
        for s in students:
            records = Attendance.objects.filter(student=s, date__range=[start_date, end_date])
            total = records.count()
            present = records.filter(status='present').count()
            data.append({
                'student': s,
                'total': total,
                'present': present,
                'absent': records.filter(status='absent').count(),
                'late': records.filter(status='late').count(),
                'rate': round(present / total * 100, 1) if total else 0,
            })
        return render(request, self.template_name, {
            'attendance_data': data,
            'start_date': start_date,
            'end_date': end_date,
        })
#---------------------------------------------------------------------------------------------------

class BulkAttendanceView(AttendanceMarkView):
    """Alias for bulk attendance marking."""
    pass
#---------------------------------------------------------------------------------------------------

# --- Ticket Management (Teacher) ---

class TicketListViewTeacher(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    model = AssignmentTicket
    template_name = 'teacher/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        return AssignmentTicket.objects.filter(
            assignment__created_by=self.request.user
        ).select_related('student__user', 'assignment').order_by('-created_at')
#---------------------------------------------------------------------------------------------------

class TicketResponseView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/ticket_respond.html'

    def get(self, request, pk):
        ticket = get_object_or_404(AssignmentTicket, pk=pk)
        form = TicketResponseForm(instance=ticket)
        return render(request, self.template_name, {'ticket': ticket, 'form': form})

    def post(self, request, pk):
        ticket = get_object_or_404(AssignmentTicket, pk=pk)
        form = TicketResponseForm(request.POST, instance=ticket)
        if form.is_valid():
            t = form.save(commit=False)
            if t.status in ('verified', 'rejected', 'closed'):
                t.resolved_at = timezone.now()
                t.resolved_by = request.user
            t.save()
            messages.success(request, 'Ticket updated!')
            return redirect('teacher_tickets')
        return render(request, self.template_name, {'ticket': ticket, 'form': form})


# --- Brush-Up (Teacher) ---

class BrushUpRequestListViewTeacher(LoginRequiredMixin, TeacherRequiredMixin, ListView):
    model = BrushUpRequest
    template_name = 'teacher/brushup_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return BrushUpRequest.objects.filter(
            topic__created_by=self.request.user
        ).select_related('student__user', 'topic').order_by('-created_at')
#---------------------------------------------------------------------------------------------------

class BrushUpResponseView(LoginRequiredMixin, TeacherRequiredMixin, View):
    template_name = 'teacher/brushup_respond.html'

    def get(self, request, pk):
        req = get_object_or_404(BrushUpRequest, pk=pk)
        form = BrushUpResponseForm(instance=req)
        return render(request, self.template_name, {'brushup_request': req, 'form': form})

    def post(self, request, pk):
        req = get_object_or_404(BrushUpRequest, pk=pk)
        form = BrushUpResponseForm(request.POST, instance=req)
        if form.is_valid():
            form.save()
            messages.success(request, 'Response saved!')
            return redirect('teacher_brushup_requests')
        return render(request, self.template_name, {'brushup_request': req, 'form': form})


# ============================================================================
# PARENT VIEWS
# ============================================================================

class ParentDashboardView(LoginRequiredMixin, ParentRequiredMixin, View):
    template_name = 'parent/dashboard.html'

    def get(self, request):
        children = Student.objects.filter(parent=request.user).select_related('user')
        holidays = Holiday.objects.filter(date__gte=date.today()).order_by('date')[:5]
        status_posts = StatusPost.objects.filter(
            target_role__in=['all', 'parent']
        ).order_by('-is_pinned', '-created_at')[:5]

        children_data = []
        for child in children:
            submissions = Submission.objects.filter(student=child)
            children_data.append({
                'student': child,
                'total_assignments': submissions.count(),
                'completed': submissions.filter(status='graded').count(),
                'pending': submissions.filter(status='submitted').count(),
                'not_submitted': submissions.filter(status='not_submitted').count(),
                'average_score': round(
                    submissions.filter(status='graded', score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0, 2
                ),
                'recent_scores': TestScore.objects.filter(student=child).order_by('-date')[:3],
            })

        return render(request, self.template_name, {
            'children_data': children_data,
            'holidays': holidays,
            'status_posts': status_posts,
        })


class ParentStudentProgressView(LoginRequiredMixin, ParentRequiredMixin, View):
    template_name = 'parent/student_progress.html'

    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id, parent=request.user)
        submissions = Submission.objects.filter(student=student, status='graded', score__isnull=False)
        test_scores = TestScore.objects.filter(student=student).order_by('-date')

        monthly = list(
            submissions.annotate(month=TruncMonth('submitted_at'))
            .values('month').annotate(avg=Avg('score')).order_by('month')
        )

        return render(request, self.template_name, {
            'student': student,
            'monthly_data': json.dumps(monthly, default=str),
            'test_scores': test_scores,
            'avg_score': round(submissions.aggregate(Avg('score'))['score__avg'] or 0, 2),
        })


class ParentAssignmentStatusView(LoginRequiredMixin, ParentRequiredMixin, View):
    template_name = 'parent/assignment_status.html'

    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id, parent=request.user)
        submissions = Submission.objects.filter(student=student).select_related('assignment').order_by('-submitted_at')
        return render(request, self.template_name, {'student': student, 'submissions': submissions})


class ParentRoadmapView(LoginRequiredMixin, ParentRequiredMixin, View):
    template_name = 'parent/roadmap.html'

    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id, parent=request.user)
        topics = RoadmapTopic.objects.all().order_by('order')
        tree_data = _build_topic_tree(topics)
        completed = topics.filter(status='completed').count()
        total = topics.count()
        return render(request, self.template_name, {
            'student': student,
            'tree_data': json.dumps(tree_data),
            'completed_count': completed,
            'total_count': total,
            'progress_percentage': round(completed / total * 100, 1) if total else 0,
        })


class ParentStudentAttendanceView(LoginRequiredMixin, View):
    template_name = 'parent/student_attendance.html'
    
    def get(self, request, *args, **kwargs):
        try:
            # Get the student - adjust based on your URL pattern
            student = get_object_or_404(Student, pk=kwargs.get('student_id'))
            
            # Verify this parent is allowed to view this student
            if hasattr(request.user, 'profile') and request.user.profile.role == 'parent':
                if student.parent != request.user:
                    return HttpResponseForbidden("You don't have permission to view this student")
            
            # Get attendance records - DON'T slice before filtering
            records = Attendance.objects.filter(student=student)
            
            # Now filter
            present = records.filter(status='present').count()
            absent = records.filter(status='absent').count()
            total = present + absent
            
            # Now you can slice if needed for recent records
            recent_records = records.order_by('-date')[:10]
            
            # Calculate percentage
            percentage = 0
            if total > 0:
                percentage = (present / total * 100)
            
            context = {
                'student': student,
                'present': present,
                'absent': absent,
                'total': total,
                'percentage': percentage,
                'recent_records': recent_records,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            print(f"Error in parent attendance view: {e}")
            return render(request, self.template_name, {'error': str(e)})


class ParentAttendanceView(ParentStudentAttendanceView):
    """Alias for ParentStudentAttendanceView for URL compatibility"""
    pass


class ParentFeedbackView(LoginRequiredMixin, ParentRequiredMixin, View):
    template_name = 'parent/feedback.html'

    def get(self, request):
        feedbacks = Feedback.objects.filter(submitted_by=request.user).order_by('-created_at')
        form = FeedbackForm()
        return render(request, self.template_name, {'feedbacks': feedbacks, 'form': form})

    def post(self, request):
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.submitted_by = request.user
            fb.save()
            messages.success(request, 'Feedback submitted!')
            return redirect('parent_feedback')
        feedbacks = Feedback.objects.filter(submitted_by=request.user)
        return render(request, self.template_name, {'feedbacks': feedbacks, 'form': form})


# ============================================================================
# STUDENT VIEWS
# ============================================================================

class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, View):
    template_name = 'student/dashboard.html'

    def get(self, request):
        student = request.user.student
        all_submissions = Submission.objects.filter(student=student)
        submitted_ids = all_submissions.filter(
            status__in=['submitted', 'graded']
        ).values_list('assignment_id', flat=True)

        pending = Assignment.objects.filter(
            status='active', due_date__gte=date.today()
        ).exclude(id__in=submitted_ids)

        overdue = Assignment.objects.filter(
            status='active', due_date__lt=date.today()
        ).exclude(id__in=submitted_ids)

        avg_score = all_submissions.filter(
            status='graded', score__isnull=False
        ).aggregate(Avg('score'))['score__avg'] or 0

        status_posts = StatusPost.objects.filter(
            target_role__in=['all', 'student']
        ).order_by('-is_pinned', '-created_at')[:5]

        holidays = Holiday.objects.filter(date__gte=date.today()).order_by('date')[:5]

        return render(request, self.template_name, {
            'completed_assignments': all_submissions.filter(status='graded'),
            'pending_assignments': pending,
            'overdue_assignments': overdue,
            'submitted_assignments': all_submissions.filter(status='submitted'),
            'average_score': round(avg_score, 2),
            'total_assignments': all_submissions.count(),
            'status_posts': status_posts,
            'holidays': holidays,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        })


class StudentAssignmentListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = Assignment
    template_name = 'student/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        return Assignment.objects.filter(status='active').order_by('due_date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.request.user.student
        submitted_ids = Submission.objects.filter(
            student=student
        ).exclude(status='not_submitted').values_list('assignment_id', flat=True)
        ctx['submitted_ids'] = set(submitted_ids)
        return ctx


class StudentAssignmentDetailView(LoginRequiredMixin, StudentRequiredMixin, View):
    template_name = 'student/assignment_detail.html'

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        student = request.user.student
        submission = Submission.objects.filter(assignment=assignment, student=student).first()
        return render(request, self.template_name, {
            'assignment': assignment,
            'submission': submission,
        })


class StudentSubmissionCreateView(LoginRequiredMixin, StudentRequiredMixin, View):
    template_name = 'student/submit_assignment.html'

    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        form = SubmissionForm()
        return render(request, self.template_name, {'assignment': assignment, 'form': form})

    def post(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        student = request.user.student
        form = SubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            submission, _ = Submission.objects.get_or_create(
                assignment=assignment,
                student=student,
                defaults={'status': 'not_submitted'}
            )
            submission.file = form.cleaned_data.get('file') or submission.file
            submission.submission_text = form.cleaned_data.get('submission_text', '')
            submission.submission_method = form.cleaned_data.get('submission_method', 'online')
            submission.status = 'submitted'
            submission.submitted_at = timezone.now()
            submission.save()
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('student_dashboard')

        return render(request, self.template_name, {'assignment': assignment, 'form': form})


class StudentProgressView(LoginRequiredMixin, StudentRequiredMixin, View):
    """Progress form with graph and progress card per topic."""
    template_name = 'student/progress.html'

    def get(self, request):
        student = request.user.student
        submissions = Submission.objects.filter(student=student, status='graded', score__isnull=False)

        monthly = list(
            submissions.annotate(month=TruncMonth('submitted_at'))
            .values('month').annotate(avg=Avg('score'), count=Count('id')).order_by('month')
        )

        test_scores = TestScore.objects.filter(student=student).order_by('-date')
        topics = RoadmapTopic.objects.all()
        topic_progress = {}
        for topic in topics:
            topic_progress[topic.title] = {
                'status': topic.status,
                'badge_class': topic.get_badge_class(),
                'completion': {'completed': 100, 'in_progress': 50, 'upcoming': 10, 'not_started': 0}.get(topic.status, 0),
            }

        avg = submissions.aggregate(Avg('score'))['score__avg'] or 0

        return render(request, self.template_name, {
            'monthly_scores': json.dumps(monthly, default=str),
            'topic_progress': json.dumps(topic_progress),
            'topic_progress_raw': list(topic_progress.items()),
            'test_scores': test_scores[:10],
            'total_assignments': submissions.count(),
            'average_score': round(avg, 2),
            'attendance_rate': student.get_attendance_rate(),
        })


class StudentRoadmapView(LoginRequiredMixin, StudentRequiredMixin, View):
    """
    Roadmap as tree view with future topics, test dates visible.
    Student can request brush-up from here.
    """
    template_name = 'student/roadmap.html'

    def get(self, request):
        topics = RoadmapTopic.objects.all().order_by('order')
        tree_data = _build_topic_tree(topics, include_tests=True)
        completed = topics.filter(status='completed').count()
        total = topics.count()
        return render(request, self.template_name, {
            'tree_data': json.dumps(tree_data),
            'completion_percentage': round(completed / total * 100, 1) if total else 0,
            'completed_topics': completed,
            'total_topics': total,
        })


class StudentAttendanceView(LoginRequiredMixin, View):
    template_name = 'student/attendance.html'
    
    def get(self, request, *args, **kwargs):
        try:
            # Get the student - adjust based on how you're getting the student
            # Option 1: If using DetailView with pk
            student = get_object_or_404(Student, pk=kwargs.get('pk'))
            
            # Option 2: If getting from logged-in user
            # student = request.user.student_profile  # or however you access it
            
            # Get attendance records - DON'T slice before filtering
            records = Attendance.objects.filter(student=student)
            
            # Now filter
            present = records.filter(status='present').count()
            absent = records.filter(status='absent').count()
            total = present + absent
            
            # Now you can slice if needed for recent records
            recent_records = records.order_by('-date')[:10]
            
            # Calculate percentage
            percentage = 0
            if total > 0:
                percentage = (present / total * 100)
            
            context = {
                'student': student,
                'present': present,
                'absent': absent,
                'total': total,
                'percentage': percentage,
                'recent_records': recent_records,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            print(f"Error in student attendance view: {e}")
            return render(request, self.template_name, {'error': str(e)})


class StudentTestScoresView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = TestScore
    template_name = 'student/test_scores.html'
    context_object_name = 'test_scores'
    paginate_by = 20

    def get_queryset(self):
        return TestScore.objects.filter(student=self.request.user.student).order_by('-date')


# --- Tickets ---

class RaiseTicketView(LoginRequiredMixin, StudentRequiredMixin, View):
    """Student raises a ticket after submitting via email/WhatsApp/physical."""
    template_name = 'student/raise_ticket.html'

    def get(self, request):
        form = AssignmentTicketForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AssignmentTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.student = request.user.student
            ticket.save()
            messages.success(request, 'Ticket raised! Teacher will review it soon.')
            return redirect('ticket_list')
        return render(request, self.template_name, {'form': form})


class TicketListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = AssignmentTicket
    template_name = 'student/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        return AssignmentTicket.objects.filter(
            student=self.request.user.student
        ).select_related('assignment').order_by('-created_at')


class TicketDetailView(LoginRequiredMixin, StudentRequiredMixin, View):
    template_name = 'student/ticket_detail.html'

    def get(self, request, pk):
        ticket = get_object_or_404(AssignmentTicket, pk=pk, student=request.user.student)
        return render(request, self.template_name, {'ticket': ticket})


# --- Brush-up / Retest ---

class BrushUpRequestView(LoginRequiredMixin, StudentRequiredMixin, View):
    """Student requests brush-up or re-test from roadmap."""
    template_name = 'student/brushup_request.html'

    def get(self, request):
        form = BrushUpRequestForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BrushUpRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.student = request.user.student
            req.save()
            label = 'Brush-up session' if req.request_type == 'brushup' else 'Re-test'
            messages.success(request, f'{label} request submitted!')
            return redirect('brushup_list')
        return render(request, self.template_name, {'form': form})


class BrushUpRequestListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    model = BrushUpRequest
    template_name = 'student/brushup_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return BrushUpRequest.objects.filter(
            student=self.request.user.student
        ).order_by('-created_at')


class RetestRequestView(LoginRequiredMixin, StudentRequiredMixin, View):
    """Apply for re-test from a failed test entry."""
    template_name = 'student/retest_request.html'

    def get(self, request, test_id):
        test = get_object_or_404(TestScore, pk=test_id, student=request.user.student)
        return render(request, self.template_name, {'test': test})

    def post(self, request, test_id):
        test = get_object_or_404(TestScore, pk=test_id, student=request.user.student)
        reason = request.POST.get('reason', '')
        if test.roadmap_topic:
            BrushUpRequest.objects.create(
                student=request.user.student,
                topic=test.roadmap_topic,
                request_type='retest',
                reason=reason or f'Re-test request for {test.test_name}'
            )
            messages.success(request, 'Re-test request submitted!')
        else:
            messages.error(request, 'No roadmap topic linked to this test.')
        return redirect('brushup_list')


# ============================================================================
# API ENDPOINTS
# ============================================================================

class RoadmapTreeAPIView(LoginRequiredMixin, View):
    def get(self, request, teacher_id=None):
        if teacher_id:
            topics = RoadmapTopic.objects.filter(created_by_id=teacher_id).order_by('order')
        else:
            topics = RoadmapTopic.objects.all().order_by('order')
        return JsonResponse(_build_topic_tree(topics, include_tests=True), safe=False)


class AssignmentStatusAPIView(LoginRequiredMixin, View):
    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        return JsonResponse(assignment.get_submission_stats())


class StudentProgressAPIView(LoginRequiredMixin, View):
    def get(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
            submissions = Submission.objects.filter(student=student)
            return JsonResponse({
                'total': submissions.count(),
                'graded': submissions.filter(status='graded').count(),
                'pending': submissions.filter(status='submitted').count(),
                'average_score': round(
                    submissions.filter(status='graded', score__isnull=False)
                    .aggregate(Avg('score'))['score__avg'] or 0, 2
                ),
            })
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Not found'}, status=404)


class AttendanceAPIView(LoginRequiredMixin, View):
    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)
        records = Attendance.objects.filter(student=student).order_by('-date')[:30]
        data = [
            {'date': str(r.date), 'status': r.status}
            for r in records
        ]
        return JsonResponse(data, safe=False)


class NotificationCountAPIView(LoginRequiredMixin, View):
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})


# ============================================================================
# HELPERS
# ============================================================================

def _build_topic_tree(topics, include_tests=False):
    """
    Build hierarchical tree JSON from a queryset of RoadmapTopic.
    Used by all roadmap views.
    """
    topic_dict = {}
    for topic in topics:
        node = {
            'id': topic.id,
            'name': topic.title,
            'status': topic.status,
            'badge_class': topic.get_badge_class(),
            'description': topic.description,
            'children': [],
        }
        if include_tests:
            node['test_scheduled'] = str(topic.test_scheduled) if topic.test_scheduled else None
            node['test_title'] = topic.test_title
            node['has_upcoming_test'] = topic.has_upcoming_test()
        topic_dict[topic.id] = node

    tree = []
    for topic in topics:
        if topic.parent_topic_id and topic.parent_topic_id in topic_dict:
            topic_dict[topic.parent_topic_id]['children'].append(topic_dict[topic.id])
        else:
            tree.append(topic_dict[topic.id])

    return tree
