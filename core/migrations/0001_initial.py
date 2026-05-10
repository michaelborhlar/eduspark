from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    """
    Hand-written initial migration.
    Student does NOT use PermissionsMixin so there is zero dependency
    on auth.Group or auth.Permission — this migration has NO auth dependency
    and works on any Django version / Python version.
    """

    initial = True
    dependencies = []   # ← empty: no auth dependency needed at all

    operations = [

        # Subject
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),

        # Student  (no groups / user_permissions fields — no auth.Group needed)
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('first_name', models.CharField(max_length=100)),
                ('surname', models.CharField(max_length=100)),
                ('email', models.EmailField(blank=True, null=True)),
                ('student_class', models.CharField(max_length=10, choices=[
                    ('SSS1','SSS 1'),('SSS2','SSS 2'),('SSS3','SSS 3'),
                    ('JSS1','JSS 1'),('JSS2','JSS 2'),('JSS3','JSS 3'),
                    ('PRI5','Primary 5'),('PRI6','Primary 6'),
                ])),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={'ordering': ['surname', 'first_name']},
        ),

        # ClassRoster
        migrations.CreateModel(
            name='ClassRoster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('student_class', models.CharField(max_length=10, choices=[
                    ('SSS1','SSS 1'),('SSS2','SSS 2'),('SSS3','SSS 3'),
                    ('JSS1','JSS 1'),('JSS2','JSS 2'),('JSS3','JSS 3'),
                    ('PRI5','Primary 5'),('PRI6','Primary 6'),
                ])),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='roster', to='core.student')),
            ],
        ),

        # Question
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='questions/')),
                ('answer_type', models.CharField(max_length=20, default='mcq', choices=[
                    ('mcq','Multiple Choice'),('typed','Typed Answer'),('typed_image','Typed + Image Upload'),
                ])),
                ('explanation', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subject', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='questions', to='core.subject')),
            ],
        ),

        # MCQOption
        migrations.CreateModel(
            name='MCQOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('text', models.CharField(max_length=500)),
                ('is_correct', models.BooleanField(default=False)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='options', to='core.question')),
            ],
            options={'ordering': ['order']},
        ),

        # Activity
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('activity_type', models.CharField(max_length=20, choices=[
                    ('test','Test'),('assignment','Weekly Assignment'),('assessment','Weekly Assessment'),
                ])),
                ('target_class', models.CharField(max_length=10, default='ALL', choices=[
                    ('SSS1','SSS 1'),('SSS2','SSS 2'),('SSS3','SSS 3'),
                    ('JSS1','JSS 1'),('JSS2','JSS 2'),('JSS3','JSS 3'),
                    ('PRI5','Primary 5'),('PRI6','Primary 6'),('ALL','All Classes'),
                ])),
                ('answer_type', models.CharField(max_length=20, default='mcq', choices=[
                    ('mcq','Multiple Choice'),('typed','Typed Answer'),('typed_image','Typed + Image Upload'),
                ])),
                ('draw_from_bank', models.BooleanField(default=True)),
                ('question_count', models.PositiveIntegerField(default=10)),
                ('randomise_values', models.BooleanField(default=True)),
                ('randomise_order', models.BooleanField(default=True)),
                ('randomise_options', models.BooleanField(default=True)),
                ('time_limit_minutes', models.PositiveIntegerField(null=True, blank=True)),
                ('open_datetime', models.DateTimeField(null=True, blank=True)),
                ('close_datetime', models.DateTimeField(null=True, blank=True)),
                ('show_answers', models.BooleanField(default=False)),
                ('require_image', models.BooleanField(default=False)),
                ('allow_back', models.BooleanField(default=True)),
                ('is_published', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subject', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='core.subject')),
            ],
        ),

        # ActivityQuestion
        migrations.CreateModel(
            name='ActivityQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('activity', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='direct_questions', to='core.activity')),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to='core.question')),
            ],
            options={'ordering': ['order']},
        ),

        # LearningVideo
        migrations.CreateModel(
            name='LearningVideo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('target_class', models.CharField(max_length=10, default='ALL', choices=[
                    ('SSS1','SSS 1'),('SSS2','SSS 2'),('SSS3','SSS 3'),
                    ('JSS1','JSS 1'),('JSS2','JSS 2'),('JSS3','JSS 3'),
                    ('PRI5','Primary 5'),('PRI6','Primary 6'),('ALL','All Classes'),
                ])),
                ('video_file', models.FileField(blank=True, null=True, upload_to='videos/')),
                ('external_url', models.URLField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('is_visible', models.BooleanField(default=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('subject', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='core.subject')),
            ],
        ),

        # Attempt
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(null=True, blank=True)),
                ('score', models.FloatField(null=True, blank=True)),
                ('is_graded', models.BooleanField(default=False)),
                ('question_seed', models.BigIntegerField(default=0)),
                ('activity', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempts', to='core.activity')),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempts', to='core.student')),
            ],
            options={'unique_together': {('student', 'activity')}},
        ),

        # Answer
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('typed_answer', models.TextField(blank=True)),
                ('uploaded_image', models.ImageField(blank=True, null=True, upload_to='answers/')),
                ('is_correct', models.BooleanField(null=True, blank=True)),
                ('teacher_grade', models.CharField(max_length=50, blank=True)),
                ('teacher_feedback', models.TextField(blank=True)),
                ('attempt', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='answers', to='core.attempt')),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to='core.question')),
                ('selected_option', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to='core.mcqoption')),
            ],
        ),
    ]
