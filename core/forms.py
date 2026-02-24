from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import date
from django.forms.widgets import SelectDateWidget

from .models import (
    UserProfile, Student, Assignment, Submission,
    RoadmapTopic, Comment, StatusPost, Holiday,
    Attendance, AssignmentTicket, BrushUpRequest,
    Feedback, TestScore, Notification
)
_current_year = date.today().year

DATE_WIDGET = SelectDateWidget(
    years=range(_current_year + 5, 1949, -1),
    attrs={'class': 'form-select d-inline-block w-auto me-1'}
)

FUTURE_DATE_WIDGET = SelectDateWidget(
    years=range(_current_year, _current_year + 10),
    attrs={'class': 'form-select d-inline-block w-auto me-1'}
)

# =====================
# PROFILE FORMS (all roles)
# =====================

class ProfilePhotoForm(forms.ModelForm):
    """Update profile photo — available to all roles."""
    class Meta:
        model = UserProfile
        fields = ['profile_photo']
        widgets = {
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


class ProfileUpdateForm(forms.ModelForm):
    """Update basic profile info — password change handled separately via Django auth."""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'date_of_birth', 'address']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': DATE_WIDGET,
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserNameForm(forms.ModelForm):
    """Edit name/email portion of a user."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


# =====================
# STUDENT FORM 
# =====================
class StudentForm(forms.Form):
    """
    Student creation form with all fields.
    Uses plain Form (not ModelForm) with manual save() in atomic transaction.
    """

    SECTION_CHOICES = [
        ('', 'Select Section'),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('', 'Select Blood Group (Optional)'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    # ── User fields ──────────────────────────────────────────────────────────

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autocomplete': 'off'
        }),
        help_text='Must be unique'
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password (min 8 chars)'
        }),
        help_text='Minimum 8 characters'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    # ── Student fields ───────────────────────────────────────────────────────

    roll_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Auto-generated if left blank'
        }),
        help_text='Leave blank to auto-assign next available number'
    )
    grade = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Grade (e.g. 10)'
        })
    )
    section = forms.ChoiceField(
        choices=SECTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '00-00-00-0000',
            'id': 'id_phone_number'
        }),
        help_text='Format: 00-00-00-0000. Leave blank to fill later.'
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Residential Address (can be filled later)',
            'rows': 3
        }),
        help_text='Leave blank to fill later.'
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text='Select subjects this student is enrolled in'
    )
    parent = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='— Select Parent (Optional) —',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    medical_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any medical conditions (optional)'
        })
    )
    admission_date = forms.DateField(
        required=False,
        initial=date.today,
        widget=DATE_WIDGET
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load parents dropdown
        self.fields['parent'].queryset = User.objects.filter(
            profile__role='parent'
        ).order_by('first_name', 'last_name')
        # Load subjects
        from core.models import Subject
        self.fields['subjects'].queryset = Subject.objects.select_related('teacher').all().order_by('name')

    # ── Validation ───────────────────────────────────────────────────────────

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError('Passwords do not match.')
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username already taken. Choose another.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already registered.')
        return email

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number', '').strip()
        if roll_number and Student.objects.filter(roll_number=roll_number).exists():
            raise ValidationError('Roll number already exists.')
        return roll_number

    # ── Save ─────────────────────────────────────────────────────────────────

    def save(self):
        """
        Wrapped in transaction.atomic() to prevent partial saves.
        Signals are intentionally avoided for UserProfile creation here.
        """
        with transaction.atomic():

            # Auto-generate roll number if blank
            roll_number = self.cleaned_data.get('roll_number', '').strip()
            if not roll_number:
                rolls = Student.objects.values_list('roll_number', flat=True)
                numeric_rolls = []
                for r in rolls:
                    r_stripped = r.lstrip('Ss')
                    if r_stripped.isdigit():
                        numeric_rolls.append(int(r_stripped))
                next_num = max(numeric_rolls) + 1 if numeric_rolls else 1
                roll_number = f'S{str(next_num).zfill(3)}'

            # 1. Create User
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password']
            )

            # 2. Create/update UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': 'student'}
            )

            # 3. Create Student
            student = Student.objects.create(
                user=user,
                roll_number=roll_number,
                grade=self.cleaned_data['grade'],
                section=self.cleaned_data['section'],
                phone_number=self.cleaned_data.get('phone_number') or '00-000-000-000',
                address=self.cleaned_data.get('address') or 'Not provided',
                parent=self.cleaned_data.get('parent'),
                blood_group=self.cleaned_data.get('blood_group', ''),
                medical_conditions=self.cleaned_data.get('medical_conditions', ''),
                admission_date=self.cleaned_data.get('admission_date') or date.today(),
            )

            # 4. Enrol student in selected subjects
            subjects = self.cleaned_data.get('subjects', [])
            if subjects:
                from core.models import SubjectsTaken
                SubjectsTaken.objects.bulk_create([
                    SubjectsTaken(student=student, subject=subject)
                    for subject in subjects
                ])

            return student


# =====================
# PARENT FORM — FIXED
# =====================

class ParentForm(forms.Form):
    """
    FIXED: Parent creation — same atomic pattern as StudentForm.
    """

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autocomplete': 'off'})
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise ValidationError('Passwords do not match.')
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already registered.')
        return email

    def save(self):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password']
            )
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': 'parent',
                    'phone_number': self.cleaned_data.get('phone_number', '')
                }
            )
            return user


# =====================
# TEACHER FORM
# =====================

class TeacherForm(forms.Form):
    """Create a teacher account (admin only)."""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    subject_specialty = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Specialty'})
    )
    salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        help_text='Monthly salary in ₹. Can be updated later.'
    )

    QUALIFICATION_CHOICES = [
        ('', 'Select Qualification'),
        ('b_ed', 'B.Ed'),
        ('b_sc', 'B.Sc'),
        ('b_a',  'B.A'),
        ('m_sc', 'M.Sc'),
        ('m_a',  'M.A'),
        ('m_ed', 'M.Ed'),
        ('phd',  'Ph.D'),
        ('other','Other'),
    ]
    qualification = forms.ChoiceField(
        choices=QUALIFICATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    joining_date = forms.DateField(
        required=False,
        initial=date.today,
        widget=DATE_WIDGET
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username already taken.')
        return username

    def save(self):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=self.cleaned_data['password']
            )
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': 'teacher'}
            )
            # Create TeacherProfile with salary and qualification
        try:
            from core.models import TeacherProfile
            profile = UserProfile.objects.get(user=user)
            TeacherProfile.objects.get_or_create(
                user_profile=profile,
                defaults={
                    'salary': self.cleaned_data.get('salary') or 0,
                    'qualification': self.cleaned_data.get('qualification') or '',
                    'joining_date': self.cleaned_data.get('joining_date') or date.today(),
                }
            )
        except Exception:
            pass  # TeacherProfile is optional - don't fail teacher creation

        return user

# =====================
# ASSIGNMENT FORM — FIXED
# =====================

class AssignmentForm(forms.ModelForm):
    """
    FIXED: Assignment creation with PDF/DOC file upload.
    Removed buggy inline error suppression — errors now surfaced properly.
    """

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'subject', 'grade', 'due_date',
                  'max_score', 'status', 'assignment_file', 'instructions']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assignment Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Grade'}),
            'due_date': FUTURE_DATE_WIDGET,
            'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assignment_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < date.today():
            raise ValidationError('Due date cannot be in the past.')
        return due_date


# =====================
# SUBMISSION FORM
# =====================

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file', 'submission_text', 'submission_method']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'submission_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'submission_method': forms.Select(attrs={'class': 'form-control'}),
        }


# =====================
# ROADMAP TOPIC FORM
# =====================

class RoadmapTopicForm(forms.ModelForm):
    """
    Roadmap topic creation with date selector for upload date and test scheduling.
    Supports parent/child hierarchy.
    """

    class Meta:
        model = RoadmapTopic
        fields = ['title', 'description', 'parent_topic', 'order', 'status',
                  'subject', 'grade', 'estimated_hours', 'resources',
                  'test_scheduled', 'test_title', 'test_duration']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent_topic': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'resources': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'test_scheduled': FUTURE_DATE_WIDGET,
            'test_title': forms.TextInput(attrs={'class': 'form-control'}),
            'test_duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_topic'].required = False
        self.fields['parent_topic'].empty_label = '-- No Parent (Root Topic) --'
        if user:
            # Only show current teacher's topics as parent options
            self.fields['parent_topic'].queryset = RoadmapTopic.objects.filter(created_by=user)


# =====================
# ATTENDANCE FORM
# =====================

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'notes', 'time_in', 'time_out']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': DATE_WIDGET,
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'time_in': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'time_out': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


# =====================
# COMMENT FORM
# =====================

class CommentForm(forms.ModelForm):
    """
    Comment form for admin/teacher — can post on student, parent, teacher dashboards.
    """
    class Meta:
        model = Comment
        fields = ['content', 'comment_type', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment...'
            }),
            'comment_type': forms.Select(attrs={'class': 'form-control'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =====================
# STATUS POST FORM
# =====================

class StatusPostForm(forms.ModelForm):
    """Microblog post by admin — visible on dashboards."""
    class Meta:
        model = StatusPost
        fields = ['content', 'target_role', 'is_pinned']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a status update...',
                'maxlength': '500'
            }),
            'target_role': forms.Select(attrs={'class': 'form-control'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =====================
# HOLIDAY FORM
# =====================

class HolidayForm(forms.ModelForm):
    """Admin broadcasts holidays and working days to all users."""
    class Meta:
        model = Holiday
        fields = ['title', 'date', 'end_date', 'description', 'holiday_type', 'is_recurring']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': FUTURE_DATE_WIDGET,
            'end_date': FUTURE_DATE_WIDGET,
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'holiday_type': forms.Select(attrs={'class': 'form-control'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =====================
# TICKET FORM (Student)
# =====================

class AssignmentTicketForm(forms.ModelForm):
    """Student raises a ticket for offline assignment submission."""
    class Meta:
        model = AssignmentTicket
        fields = ['assignment', 'submission_method', 'details']
        widgets = {
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'submission_method': forms.Select(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe how you submitted: email address used, WhatsApp timestamp, physical drop date, etc.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignment'].queryset = Assignment.objects.filter(status='active')


# =====================
# BRUSH-UP REQUEST FORM (Student)
# =====================

class BrushUpRequestForm(forms.ModelForm):
    """Student requests a brush-up or re-test from the roadmap."""
    class Meta:
        model = BrushUpRequest
        fields = ['topic', 'request_type', 'reason']
        widgets = {
            'topic': forms.Select(attrs={'class': 'form-control'}),
            'request_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain why you need this session...'
            }),
        }


# =====================
# FEEDBACK FORM
# =====================

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'subject', 'message']
        widgets = {
            'feedback_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


# =====================
# GRADING FORM
# =====================

class GradeSubmissionForm(forms.Form):
    """Teacher grades a student submission."""
    score = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Score'})
    )
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Feedback for student'})
    )
    status = forms.ChoiceField(
        choices=[('graded', 'Graded'), ('resubmit', 'Needs Resubmission')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# =====================
# TICKET RESPONSE FORM (Teacher)
# =====================

class TicketResponseForm(forms.ModelForm):
    class Meta:
        model = AssignmentTicket
        fields = ['status', 'teacher_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'teacher_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# =====================
# BRUSH-UP RESPONSE FORM (Teacher)
# =====================

class BrushUpResponseForm(forms.ModelForm):
    class Meta:
        model = BrushUpRequest
        fields = ['status', 'scheduled_date', 'teacher_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'teacher_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
