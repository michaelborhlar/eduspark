from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from .models import (Student, ClassRoster, Subject, Question, MCQOption,
                     Activity, ActivityQuestion, LearningVideo, Attempt, Answer)


class StudentCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model  = Student
        fields = ('first_name', 'surname', 'student_class', 'email')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StudentChangeForm(forms.ModelForm):
    class Meta:
        model  = Student
        fields = ('first_name', 'surname', 'student_class', 'email',
                  'is_active', 'is_staff', 'is_superuser')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form         = StudentChangeForm
    add_form     = StudentCreationForm
    list_display  = ['full_name', 'student_class', 'email', 'date_joined', 'is_staff']
    list_filter   = ['student_class', 'is_staff']
    search_fields = ['first_name', 'surname', 'email']
    ordering      = ['surname', 'first_name']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        ('Personal Info', {'fields': ('first_name', 'surname', 'email', 'student_class')}),
        ('Password',      {'fields': ('password',)}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates',         {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {'fields': ('first_name', 'surname', 'student_class',
                           'email', 'password1', 'password2')}),
    )

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)


@admin.register(ClassRoster)
class ClassRosterAdmin(admin.ModelAdmin):
    list_display = ['student', 'student_class', 'enrolled_at']
    list_filter  = ['student_class']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class MCQOptionInline(admin.TabularInline):
    model  = MCQOption
    extra  = 4
    fields = ['text', 'is_correct', 'order']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display  = ['short_text', 'subject', 'answer_type', 'created_at']
    list_filter   = ['subject', 'answer_type']
    search_fields = ['text']
    inlines       = [MCQOptionInline]

    def short_text(self, obj): return obj.text[:80]
    short_text.short_description = 'Question'


class ActivityQuestionInline(admin.TabularInline):
    model = ActivityQuestion
    extra = 1


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display    = ['title', 'activity_type', 'target_class', 'status', 'is_published']
    list_filter     = ['activity_type', 'target_class', 'is_published']
    search_fields   = ['title']
    readonly_fields = ['status', 'created_at']
    inlines         = [ActivityQuestionInline]
    actions         = ['publish_selected', 'unpublish_selected']

    def publish_selected(self, request, qs): qs.update(is_published=True)
    publish_selected.short_description = 'Publish selected'

    def unpublish_selected(self, request, qs): qs.update(is_published=False)
    unpublish_selected.short_description = 'Unpublish selected'


@admin.register(LearningVideo)
class LearningVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'target_class', 'is_visible', 'uploaded_at']
    list_filter  = ['subject', 'target_class', 'is_visible']


class AnswerInline(admin.TabularInline):
    model         = Answer
    extra         = 0
    readonly_fields = ['question', 'selected_option', 'typed_answer',
                       'is_correct', 'uploaded_image']
    fields        = ['question', 'selected_option', 'typed_answer',
                     'is_correct', 'teacher_grade', 'teacher_feedback', 'uploaded_image']


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display    = ['student', 'activity', 'score', 'submitted_at', 'is_graded']
    list_filter     = ['activity__activity_type', 'is_graded']
    search_fields   = ['student__first_name', 'student__surname']
    readonly_fields = ['started_at', 'submitted_at', 'question_seed']
    inlines         = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'teacher_grade']
    list_filter  = ['is_correct', 'attempt__activity']
