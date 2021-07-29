from django.urls import include
from django.urls import path

from accounts import views


urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('logout', views.LogoutSuccessfulView.as_view(),
         name='logout_successful'),
    path('register', views.RegisterView.as_view(), name='register'),
    path('validate/<str:validate_hash>', views.ValidateAccountView.as_view()),
    path('profile', views.ProfileView.as_view(), name='profile'),
]
