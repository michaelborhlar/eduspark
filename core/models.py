from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

CLASS_CHOICES = [
    ('SSS1','SSS 1'),('SSS2','SSS 2'),('SSS3','SSS 3'),
    ('JSS1','JSS 1'),('JSS2','JSS 2'),('JSS3','JSS 3'),
    ('PRI5','Primary 5'),('PRI6','Primary 6'),
]
ANSWER_CHOICES = [
    ('mcq','Multiple Choice'),
    ('typed','Typed Answer'),
    ('typed_image','Typed + Image Upload'),
]
ACTIVITY_CHOICES = [
    ('test','Test'),
    ('assignment','Weekly Assignment'),
    ('assessment','Weekly Assessment'),
]

# ── Student user ───────────────────────────────────────────
class StudentManager(BaseUserManager):
    def create_user(self, first_name, surname, student_class, password=None, **extra):
        user = self.model(first_name=first_name, surname=surname,
                          student_class=student_class, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name='Admin', surname='User',
                         student_class='SSS1', password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(first_name, surname, student_class, password, **extra)

class Student(AbstractBaseUser, PermissionsMixin):
    first_name    = models.CharField(max_length=100)
    surname       = models.CharField(max_length=100)
    email         = models.EmailField(blank=True, null=True)
    student_class = models.CharField(max_length=10, choices=CLASS_CHOICES)
    date_joined   = models.DateTimeField(default=timezone.now)
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)

    USERNAME_FIELD  = 'id'
    REQUIRED_FIELDS = ['first_name','surname','student_class']
    objects = StudentManager()

    @property
    def full_name(self): return f'{self.first_name} {self.surname}'
    def __str__(self): return f'{self.full_name} ({self.student_class})'
    class Meta: ordering = ['surname','first_name']

# ── Class Roster (auto-created on signup) ──────────────────
class ClassRoster(models.Model):
    student       = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='roster')
    student_class = models.CharField(max_length=10, choices=CLASS_CHOICES)
    enrolled_at   = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.student.full_name} → {self.student_class}'

# ── Subject ────────────────────────────────────────────────
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

# ── Question Bank ──────────────────────────────────────────
class Question(models.Model):
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    text        = models.TextField()
    image       = models.ImageField(upload_to='questions/', blank=True, null=True)
    answer_type = models.CharField(max_length=20, choices=ANSWER_CHOICES, default='mcq')
    explanation = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'[{self.subject}] {self.text[:70]}'

class MCQOption(models.Model):
    question   = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text       = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order      = models.PositiveSmallIntegerField(default=0)
    class Meta: ordering = ['order']
    def __str__(self): return f'{"✓" if self.is_correct else "✗"} {self.text[:50]}'

# ── Activity (Test / Assignment / Assessment) ──────────────
class Activity(models.Model):
    title              = models.CharField(max_length=255)
    description        = models.TextField(blank=True)
    activity_type      = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    subject            = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    target_class       = models.CharField(max_length=10,
                           choices=CLASS_CHOICES + [('ALL','All Classes')], default='ALL')
    answer_type        = models.CharField(max_length=20, choices=ANSWER_CHOICES, default='mcq')
    draw_from_bank     = models.BooleanField(default=True)
    question_count     = models.PositiveIntegerField(default=10)
    randomise_values   = models.BooleanField(default=True)
    randomise_order    = models.BooleanField(default=True)
    randomise_options  = models.BooleanField(default=True)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    open_datetime      = models.DateTimeField(null=True, blank=True)
    close_datetime     = models.DateTimeField(null=True, blank=True)
    show_answers       = models.BooleanField(default=False)
    require_image      = models.BooleanField(default=False)
    allow_back         = models.BooleanField(default=True)
    is_published       = models.BooleanField(default=False)
    created_at         = models.DateTimeField(auto_now_add=True)

    @property
    def status(self):
        now = timezone.now()
        if not self.is_published: return 'draft'
        if self.open_datetime and now < self.open_datetime: return 'upcoming'
        if self.close_datetime and now > self.close_datetime: return 'closed'
        return 'open'

    @property
    def is_open(self): return self.status == 'open'

    def __str__(self): return f'[{self.activity_type.upper()}] {self.title}'

class ActivityQuestion(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='direct_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order    = models.PositiveSmallIntegerField(default=0)
    class Meta: ordering = ['order']

# ── Learning Video ─────────────────────────────────────────
class LearningVideo(models.Model):
    title        = models.CharField(max_length=255)
    subject      = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    target_class = models.CharField(max_length=10,
                       choices=CLASS_CHOICES + [('ALL','All Classes')], default='ALL')
    video_file   = models.FileField(upload_to='videos/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    description  = models.TextField(blank=True)
    is_visible   = models.BooleanField(default=True)
    uploaded_at  = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

# ── Attempt & Answers ──────────────────────────────────────
class Attempt(models.Model):
    student       = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attempts')
    activity      = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='attempts')
    started_at    = models.DateTimeField(auto_now_add=True)
    submitted_at  = models.DateTimeField(null=True, blank=True)
    score         = models.FloatField(null=True, blank=True)
    is_graded     = models.BooleanField(default=False)
    question_seed = models.BigIntegerField(default=0)
    class Meta: unique_together = ('student','activity')
    def __str__(self): return f'{self.student} → {self.activity} | {self.score}'

class Answer(models.Model):
    attempt          = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question         = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option  = models.ForeignKey(MCQOption, null=True, blank=True, on_delete=models.SET_NULL)
    typed_answer     = models.TextField(blank=True)
    uploaded_image   = models.ImageField(upload_to='answers/', blank=True, null=True)
    is_correct       = models.BooleanField(null=True, blank=True)
    teacher_grade    = models.CharField(max_length=50, blank=True)
    teacher_feedback = models.TextField(blank=True)
    def __str__(self): return f'Q{self.question_id} | {self.attempt.student.full_name}'
