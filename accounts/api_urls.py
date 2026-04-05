from django.urls import path
from .views import (
    CreateStudentView,
    AddStudentBulkAPIView,
    AddStudentCSVAPIView,
    SchoolLoginView,
    StudentProfileView,
    UserMeView,
    ForcePasswordResetAPIView,
    AdminResetStudentPasswordAPIView,
    StudentLoginView,
    StudentProfileUpdateView
)
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
    path("create-student/", CreateStudentView.as_view(), name="create-student"),
    path("bulk-add/", AddStudentBulkAPIView.as_view(), name="bulk-add"),
    path("bulk-upload/", AddStudentCSVAPIView.as_view(), name="bulk-upload"),
    path("school-login/", SchoolLoginView.as_view(), name="school-login"),
    path("me/", UserMeView.as_view(), name="user-me"),
    path("force-reset-password/", ForcePasswordResetAPIView.as_view()),
    path("students/<int:student_id>/reset-password/",AdminResetStudentPasswordAPIView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("student/login/", StudentLoginView.as_view()),
    path("student/profile/", StudentProfileView.as_view()),
    path("student/profile/update/", StudentProfileUpdateView.as_view()),
    
]
