"""atp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from stockcheck.views import HomeView, AboutView, IndexView, HelpView, SearchView, ThankView, FeedbackView
from stockcheck import views
from django.conf.urls import include
from stockcheck.views import download_data
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('atp/admin/doc/', include('django.contrib.admindocs.urls')),
    path('atp/admin/', admin.site.urls),
    path('',IndexView.as_view(), name='index'),
    path('atp/about/', AboutView.as_view(), name='about'),
    path('atp/help/', include('docs.urls')),
    path('atp/home/', HomeView.as_view(), name='home'),
    path('thanks/', ThankView.as_view(), name='thanks'),
    path('atp/feedback/', FeedbackView.as_view(), name='feedback'),
    path('atp/login/', auth_views.LoginView.as_view(template_name="registration/login.html", redirect_authenticated_user=True), name='login'),
    path('atp/signup/', views.signup, name='signup'),
    path('atp/search/', SearchView.as_view(), name='product_details'),
    path('atp/chat/', include('chatbot.urls')),  # NLP conversational search
    path('atp/data_download/', download_data, name='download_data'),
    path('atp/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('atp/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('atp/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('atp/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('atp/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('atp/change-password/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('atp/change-password-done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# For production, we'll still add this for our Docker environment
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
