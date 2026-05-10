from rest_framework import serializers
from .models import (Student, Subject, Question, MCQOption,
                     Activity, LearningVideo, Attempt, Answer)

# ── Auth ────────────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)
    class Meta:
        model  = Student
        fields = ['first_name','surname','email','student_class','password','password2']

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({'password2':'Passwords do not match.'})
        return data

    def create(self, validated_data):
        from .models import ClassRoster
        pw = validated_data.pop('password')
        student = Student.objects.create_user(password=pw, **validated_data)
        ClassRoster.objects.create(student=student, student_class=student.student_class)
        return student

class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    class Meta:
        model  = Student
        fields = ['id','first_name','surname','full_name','email','student_class','date_joined','is_staff']

# ── Questions ───────────────────────────────────────────────
class MCQOptionStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MCQOption
        fields = ['id','text','order']

class MCQOptionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MCQOption
        fields = '__all__'

class QuestionStudentSerializer(serializers.ModelSerializer):
    options = MCQOptionStudentSerializer(many=True, read_only=True)
    class Meta:
        model  = Question
        fields = ['id','text','image','answer_type','options']

class QuestionAdminSerializer(serializers.ModelSerializer):
    options      = MCQOptionAdminSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')
    class Meta:
        model  = Question
        fields = '__all__'

# ── Subject ─────────────────────────────────────────────────
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Subject
        fields = '__all__'

# ── Activities ───────────────────────────────────────────────
class ActivitySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')
    status       = serializers.ReadOnlyField()
    is_open      = serializers.ReadOnlyField()
    submissions  = serializers.SerializerMethodField()
    class Meta:
        model  = Activity
        fields = '__all__'
    def get_submissions(self, obj):
        return obj.attempts.filter(submitted_at__isnull=False).count()

# ── Videos ──────────────────────────────────────────────────
class LearningVideoSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')
    class Meta:
        model  = LearningVideo
        fields = '__all__'

# ── Submit ───────────────────────────────────────────────────
class AnswerItemSerializer(serializers.Serializer):
    question_id        = serializers.IntegerField()
    selected_option_id = serializers.IntegerField(required=False, allow_null=True)
    typed_answer       = serializers.CharField(required=False, allow_blank=True, default='')

class AttemptSubmitSerializer(serializers.Serializer):
    answers = AnswerItemSerializer(many=True)

# ── Review ───────────────────────────────────────────────────
class AnswerReviewSerializer(serializers.ModelSerializer):
    question_text  = serializers.CharField(source='question.text', read_only=True)
    question_image = serializers.SerializerMethodField()
    student_name   = serializers.CharField(source='attempt.student.full_name', read_only=True)
    student_class  = serializers.CharField(source='attempt.student.student_class', read_only=True)
    activity_title = serializers.CharField(source='attempt.activity.title', read_only=True)
    activity_type  = serializers.CharField(source='attempt.activity.activity_type', read_only=True)
    class Meta:
        model  = Answer
        fields = ['id','question_text','question_image','typed_answer','uploaded_image',
                  'is_correct','teacher_grade','teacher_feedback',
                  'student_name','student_class','activity_title','activity_type']
    def get_question_image(self, obj):
        req = self.context.get('request')
        if obj.question.image and req:
            return req.build_absolute_uri(obj.question.image.url)
        return None

class AttemptResultSerializer(serializers.ModelSerializer):
    student_name   = serializers.CharField(source='student.full_name', read_only=True)
    activity_title = serializers.CharField(source='activity.title', read_only=True)
    activity_type  = serializers.CharField(source='activity.activity_type', read_only=True)
    show_answers   = serializers.BooleanField(source='activity.show_answers', read_only=True)
    class Meta:
        model  = Attempt
        fields = ['id','student_name','activity_title','activity_type','show_answers',
                  'started_at','submitted_at','score','is_graded']
