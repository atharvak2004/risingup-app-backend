from django.urls import path
from .views import (
    SchoolRegistrationCreateView,
    ChangePasswordView,
    GradeListView
)

urlpatterns = [
    path("school-registrations/", SchoolRegistrationCreateView.as_view(), name="school-registration-create"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("grades/", GradeListView.as_view(), name="grades"),
]
