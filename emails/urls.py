
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = "emails"

urlpatterns = [
    path("", views.home, name="home"),
    path("mine/", views.my_templates, name="my_templates"),
    path("create/", views.template_create, name="template_create"),
    path("<int:pk>/edit/", views.template_edit, name="template_edit"),
    path("<int:pk>/use/", views.template_use, name="template_use"),
    path("<int:pk>/delete/", views.template_delete, name="template_delete"),
    path("<int:pk>/preview/", views.template_preview, name="template_preview"),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
