
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup
from .views import profile_modal, profile_update
from django.conf import settings
from django.conf.urls.static import static

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", signup, name="signup"),
    
    path("profile/", profile_modal, name="profile_modal"),
    path("profile/update/", profile_update, name="profile_update"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)