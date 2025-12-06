# accounts/api_urls.py

from django.urls import path
from .views import CreateStudentView, UserMeView

urlpatterns = [
    path("create-student/", CreateStudentView.as_view(), name="create-student"),
    path("me/", UserMeView.as_view(), name="user-me"),
]
