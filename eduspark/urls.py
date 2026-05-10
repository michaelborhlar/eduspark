from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    # Django built-in admin (superuser management)
    path('django-admin/', admin.site.urls),

    # REST API
    path('api/', include('core.api_urls')),

    # ── Student Portal  →  http://localhost:8000/student/  ──
    path('student/', TemplateView.as_view(template_name='student/index.html'), name='student-portal'),

    # ── Admin Panel    →  http://localhost:8000/admin-panel/  ──
    path('admin-panel/', TemplateView.as_view(template_name='admin_panel/index.html'), name='admin-portal'),

    # Root → redirect to student portal
    path('', RedirectView.as_view(url='/student/', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
