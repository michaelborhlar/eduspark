from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/',  views.RegisterView.as_view()),
    path('auth/login/',     views.LoginView.as_view()),
    path('auth/logout/',    views.LogoutView.as_view()),
    path('auth/me/',        views.MeView.as_view()),

    # Student
    path('activities/',                                    views.ActivityListView.as_view()),
    path('activities/<int:pk>/',                           views.ActivityDetailView.as_view()),
    path('activities/<int:activity_id>/draw/',             views.DrawQuestionsView.as_view()),
    path('attempts/<int:attempt_id>/submit/',              views.SubmitAttemptView.as_view()),
    path('attempts/<int:attempt_id>/upload-image/<int:question_id>/', views.UploadAnswerImageView.as_view()),
    path('my-results/',                                    views.MyAttemptsView.as_view()),
    path('learning/',                                      views.LearningVideoListView.as_view()),

    # Admin
    path('admin/subjects/',                          views.AdminSubjectView.as_view()),
    path('admin/questions/',                         views.AdminQuestionListCreateView.as_view()),
    path('admin/questions/<int:pk>/',                views.AdminQuestionDetailView.as_view()),
    path('admin/questions/<int:question_id>/options/', views.AdminMCQOptionView.as_view()),
    path('admin/questions/<int:question_id>/options/<int:option_id>/', views.AdminMCQOptionView.as_view()),
    path('admin/activities/',                        views.AdminActivityListCreateView.as_view()),
    path('admin/activities/<int:pk>/',               views.AdminActivityDetailView.as_view()),
    path('admin/activities/<int:pk>/publish/',       views.AdminTogglePublishView.as_view()),
    path('admin/videos/',                            views.AdminVideoListCreateView.as_view()),
    path('admin/videos/<int:pk>/',                   views.AdminVideoDetailView.as_view()),
    path('admin/videos/<int:pk>/toggle/',            views.AdminToggleVideoView.as_view()),
    path('admin/submissions/',                       views.AdminSubmissionsView.as_view()),
    path('admin/grade/<int:answer_id>/',             views.AdminGradeAnswerView.as_view()),
    path('admin/roster/',                            views.AdminRosterView.as_view()),
    path('admin/grade-centre/',                      views.AdminGradeCentreView.as_view()),
    path('admin/stats/',                             views.AdminStatsView.as_view()),
]
