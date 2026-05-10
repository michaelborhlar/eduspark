import random, hashlib
from django.utils import timezone
from django.db.models import Q, Avg
from django.contrib.auth import login, logout
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import (Student, Subject, Question, MCQOption, Activity,
                     ActivityQuestion, LearningVideo, Attempt, Answer, ClassRoster)
from .serializers import (
    RegisterSerializer, StudentSerializer, QuestionAdminSerializer,
    SubjectSerializer, ActivitySerializer, LearningVideoSerializer,
    AttemptSubmitSerializer, AnswerReviewSerializer, AttemptResultSerializer,
)

# ── Auth ────────────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if ser.is_valid():
            student = ser.save()
            login(request, student, backend='django.contrib.auth.backends.ModelBackend')
            return Response(StudentSerializer(student).data, status=201)
        return Response(ser.errors, status=400)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        first = request.data.get('first_name','').strip()
        sname = request.data.get('surname','').strip()
        pwd   = request.data.get('password','')
        cls   = request.data.get('student_class','')
        qs = Student.objects.filter(first_name__iexact=first, surname__iexact=sname)
        if not qs.exists():
            return Response({'detail':'Student not found.'}, status=404)
        if qs.count() > 1 and cls:
            qs = qs.filter(student_class=cls)
        student = qs.first()
        if student and student.check_password(pwd):
            login(request, student, backend='django.contrib.auth.backends.ModelBackend')
            return Response(StudentSerializer(student).data)
        return Response({'detail':'Wrong password.'}, status=401)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail':'Logged out.'})

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(StudentSerializer(request.user).data)

# ── Student: Activities ─────────────────────────────────────
class ActivityListView(generics.ListAPIView):
    serializer_class   = ActivitySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        cls = self.request.user.student_class
        return Activity.objects.filter(is_published=True).filter(
            Q(target_class=cls)|Q(target_class='ALL')
        ).select_related('subject').order_by('-created_at')

class ActivityDetailView(generics.RetrieveAPIView):
    serializer_class   = ActivitySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        cls = self.request.user.student_class
        return Activity.objects.filter(is_published=True).filter(
            Q(target_class=cls)|Q(target_class='ALL'))

# ── Student: Draw questions (unique per student) ─────────────
class DrawQuestionsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, activity_id):
        try:
            activity = Activity.objects.get(pk=activity_id, is_published=True)
        except Activity.DoesNotExist:
            return Response({'detail':'Activity not found.'}, status=404)
        if not activity.is_open:
            return Response({'detail':'This activity is not currently open.'}, status=403)
        existing = Attempt.objects.filter(
            student=request.user, activity=activity, submitted_at__isnull=False).first()
        if existing and activity.activity_type != 'assessment':
            return Response({'detail':'You have already submitted this.'}, status=403)

        # Unique deterministic seed per student per activity
        seed = int(hashlib.sha256(
            f'{request.user.id}-{activity_id}'.encode()).hexdigest(), 16) % (2**31)

        if activity.draw_from_bank:
            pool = list(Question.objects.filter(
                subject=activity.subject).prefetch_related('options'))
            rng = random.Random(seed)
            if activity.randomise_order:
                rng.shuffle(pool)
            questions = pool[:activity.question_count]
        else:
            aq = ActivityQuestion.objects.filter(activity=activity).select_related(
                'question').prefetch_related('question__options').order_by('order')
            questions = [a.question for a in aq]
            if activity.randomise_order:
                random.Random(seed).shuffle(questions)

        data = []
        for q in questions:
            opts = list(q.options.all())
            if activity.randomise_options and opts:
                random.Random(seed + q.id).shuffle(opts)
            data.append({
                'id': q.id, 'text': q.text,
                'image': request.build_absolute_uri(q.image.url) if q.image else None,
                'answer_type': q.answer_type,
                'options': [{'id':o.id,'text':o.text} for o in opts],
            })

        attempt, _ = Attempt.objects.get_or_create(
            student=request.user, activity=activity,
            defaults={'question_seed': seed})

        return Response({
            'attempt_id': attempt.id,
            'time_limit_minutes': activity.time_limit_minutes,
            'allow_back': activity.allow_back,
            'require_image': activity.require_image,
            'questions': data,
        })

# ── Student: Submit ─────────────────────────────────────────
class SubmitAttemptView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, attempt_id):
        try:
            attempt = Attempt.objects.select_related('activity').get(
                pk=attempt_id, student=request.user)
        except Attempt.DoesNotExist:
            return Response({'detail':'Attempt not found.'}, status=404)
        if attempt.submitted_at:
            return Response({'detail':'Already submitted.'}, status=400)
        if not attempt.activity.is_open:
            return Response({'detail':'This activity has closed.'}, status=403)

        ser = AttemptSubmitSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        correct = total_mcq = 0
        for ans_data in ser.validated_data['answers']:
            try:
                q = Question.objects.get(pk=ans_data['question_id'])
            except Question.DoesNotExist:
                continue
            answer = Answer(attempt=attempt, question=q,
                            typed_answer=ans_data.get('typed_answer',''))
            opt_id = ans_data.get('selected_option_id')
            if opt_id:
                try:
                    opt = MCQOption.objects.get(pk=opt_id, question=q)
                    answer.selected_option = opt
                    answer.is_correct = opt.is_correct
                    total_mcq += 1
                    if opt.is_correct: correct += 1
                except MCQOption.DoesNotExist:
                    pass
            answer.save()

        attempt.submitted_at = timezone.now()
        if total_mcq:
            attempt.score = round(correct / total_mcq * 100, 1)
        attempt.save()

        response = {'score':attempt.score,'correct':correct,'total_mcq':total_mcq,'submitted':True}

        if attempt.activity.show_answers:
            detail = []
            for ans in attempt.answers.select_related(
                    'question','selected_option').prefetch_related('question__options'):
                correct_opt = ans.question.options.filter(is_correct=True).first()
                detail.append({
                    'question': ans.question.text,
                    'question_image': (request.build_absolute_uri(ans.question.image.url)
                                       if ans.question.image else None),
                    'your_answer': (ans.selected_option.text if ans.selected_option
                                    else ans.typed_answer or '—'),
                    'is_correct': ans.is_correct,
                    'correct_answer': correct_opt.text if correct_opt else None,
                    'explanation': ans.question.explanation,
                })
            response['answer_review'] = detail
        return Response(response)

class UploadAnswerImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]
    def post(self, request, attempt_id, question_id):
        try:
            attempt = Attempt.objects.get(pk=attempt_id, student=request.user)
            answer  = Answer.objects.get(attempt=attempt, question_id=question_id)
        except (Attempt.DoesNotExist, Answer.DoesNotExist):
            return Response({'detail':'Not found.'}, status=404)
        img = request.FILES.get('image')
        if not img:
            return Response({'detail':'No image provided.'}, status=400)
        answer.uploaded_image = img
        answer.save()
        return Response({'url': request.build_absolute_uri(answer.uploaded_image.url)})

class MyAttemptsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = AttemptResultSerializer
    def get_queryset(self):
        return Attempt.objects.filter(
            student=self.request.user, submitted_at__isnull=False
        ).select_related('activity').order_by('-submitted_at')

# ── Student: Learning ───────────────────────────────────────
class LearningVideoListView(generics.ListAPIView):
    serializer_class   = LearningVideoSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        cls = self.request.user.student_class
        return LearningVideo.objects.filter(is_visible=True).filter(
            Q(target_class=cls)|Q(target_class='ALL')).order_by('-uploaded_at')

# ── Admin: Subjects ─────────────────────────────────────────
class AdminSubjectView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = SubjectSerializer
    queryset           = Subject.objects.all()

# ── Admin: Question Bank ────────────────────────────────────
class AdminQuestionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = QuestionAdminSerializer
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    def get_queryset(self):
        qs = Question.objects.all().select_related('subject').prefetch_related('options')
        subj = self.request.query_params.get('subject','')
        atype = self.request.query_params.get('answer_type','')
        if subj: qs = qs.filter(subject__name__icontains=subj)
        if atype: qs = qs.filter(answer_type=atype)
        return qs

class AdminQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = QuestionAdminSerializer
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    queryset           = Question.objects.all().prefetch_related('options')

class AdminMCQOptionView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, question_id):
        try: q = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return Response({'detail':'Not found.'}, status=404)
        opt = MCQOption.objects.create(
            question=q, text=request.data.get('text',''),
            is_correct=request.data.get('is_correct', False),
            order=request.data.get('order', 0))
        return Response({'id':opt.id,'text':opt.text,'is_correct':opt.is_correct}, status=201)
    def delete(self, request, question_id, option_id=None):
        MCQOption.objects.filter(pk=option_id, question_id=question_id).delete()
        return Response(status=204)

# ── Admin: Activities ───────────────────────────────────────
class AdminActivityListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = ActivitySerializer
    queryset           = Activity.objects.all().select_related('subject').order_by('-created_at')

class AdminActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = ActivitySerializer
    queryset           = Activity.objects.all()

class AdminTogglePublishView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, pk):
        try: a = Activity.objects.get(pk=pk)
        except Activity.DoesNotExist:
            return Response({'detail':'Not found.'}, status=404)
        a.is_published = not a.is_published
        a.save()
        return Response({'published': a.is_published})

# ── Admin: Videos ───────────────────────────────────────────
class AdminVideoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = LearningVideoSerializer
    queryset           = LearningVideo.objects.all().order_by('-uploaded_at')
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

class AdminVideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = LearningVideoSerializer
    queryset           = LearningVideo.objects.all()
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

class AdminToggleVideoView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, pk):
        try: v = LearningVideo.objects.get(pk=pk)
        except LearningVideo.DoesNotExist:
            return Response({'detail':'Not found.'}, status=404)
        v.is_visible = not v.is_visible
        v.save()
        return Response({'is_visible': v.is_visible})

# ── Admin: Submissions & Grading ────────────────────────────
class AdminSubmissionsView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        answers = Answer.objects.filter(
            teacher_grade='',
            attempt__activity__answer_type__in=['typed','typed_image'],
            attempt__submitted_at__isnull=False,
        ).select_related('attempt__student','attempt__activity','question')
        return Response(AnswerReviewSerializer(answers, many=True,
                        context={'request':request}).data)

class AdminGradeAnswerView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, answer_id):
        try: ans = Answer.objects.get(pk=answer_id)
        except Answer.DoesNotExist:
            return Response({'detail':'Not found.'}, status=404)
        ans.teacher_grade    = request.data.get('grade','')
        ans.teacher_feedback = request.data.get('feedback','')
        ans.save()
        attempt = ans.attempt
        ungraded = attempt.answers.filter(
            teacher_grade='', question__answer_type__in=['typed','typed_image']).count()
        if ungraded == 0:
            attempt.is_graded = True; attempt.save()
        return Response({'detail':'Grade saved.'})

# ── Admin: Roster & Grade Centre ────────────────────────────
class AdminRosterView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        cls = request.query_params.get('class','')
        qs  = Student.objects.filter(is_staff=False)
        if cls: qs = qs.filter(student_class=cls)
        data = {}
        for s in qs:
            key = s.student_class
            if key not in data: data[key] = []
            avg = s.attempts.filter(submitted_at__isnull=False,
                score__isnull=False).aggregate(avg=Avg('score'))['avg']
            data[key].append({
                'id':s.id,'name':s.full_name,'email':s.email or '—',
                'date_joined':s.date_joined.strftime('%b %d, %Y'),
                'avg_score': round(avg,1) if avg else None,
                'attempts': s.attempts.filter(submitted_at__isnull=False).count(),
            })
        return Response(data)

class AdminGradeCentreView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        cls = request.query_params.get('class','')
        qs  = Attempt.objects.filter(submitted_at__isnull=False).select_related('student','activity')
        if cls: qs = qs.filter(student__student_class=cls)
        return Response([{
            'student': a.student.full_name, 'student_class': a.student.student_class,
            'activity': a.activity.title, 'activity_type': a.activity.activity_type,
            'score': a.score, 'is_graded': a.is_graded,
            'submitted_at': a.submitted_at.strftime('%b %d, %Y %H:%M') if a.submitted_at else None,
        } for a in qs.order_by('student__surname','-submitted_at')])

# ── Admin: Dashboard Stats ──────────────────────────────────
class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        now = timezone.now()
        active = Activity.objects.filter(is_published=True).filter(
            Q(open_datetime__isnull=True)|Q(open_datetime__lte=now)
        ).filter(
            Q(close_datetime__isnull=True)|Q(close_datetime__gte=now)
        ).count()
        return Response({
            'total_students': Student.objects.filter(is_staff=False).count(),
            'active_activities': active,
            'pending_reviews': Answer.objects.filter(
                teacher_grade='',
                attempt__activity__answer_type__in=['typed','typed_image'],
                attempt__submitted_at__isnull=False).count(),
            'total_submissions': Attempt.objects.filter(submitted_at__isnull=False).count(),
            'class_counts': {
                cls: Student.objects.filter(student_class=cls, is_staff=False).count()
                for cls in ['SSS1','SSS2','SSS3','JSS1','JSS2','JSS3']
            },
        })
