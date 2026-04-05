from django.urls import path

from .views import (
    AddStudentAPIView,
    ClassStudentListView,
    DeleteStudentAPIView,
    SchoolProfileAPIView,
    StudentProgressAPIView,
    ClassProgressAPIView,
    ContentAPIView,
    ReportsAPIView,
    SubscriptionDeadlineAPIView,
    ReferralAPIView,
    ContactAPIView,
    SchoolAdminDashboardAPIView,
    StudentSearchAPIView,
    StudentsYearAPIView,
    GlobalSearchAPIView,
)

urlpatterns = [

    # -------------------------
    # STUDENTS
    # -------------------------
    path("students/", ClassStudentListView.as_view(), name="students-list"),

    path("students/add/", AddStudentAPIView.as_view(), name="student-add"),

    path(
        "students/<int:student_id>/delete/",
        DeleteStudentAPIView.as_view(),
        name="student-delete",
    ),

    path(
        "students/<int:student_id>/progress/",
        StudentProgressAPIView.as_view(),
        name="student-progress",
    ),

    # -------------------------
    # CLASS / SECTION
    # -------------------------
    path(
        "classes/<int:grade_id>/<int:section_id>/students/",
        ClassStudentListView.as_view(),
        name="class-students",
    ),

    path(
        "classes/<int:grade_id>/<int:section_id>/progress/",
        ClassProgressAPIView.as_view(),
        name="class-progress",
    ),

    # -------------------------
    # CONTENT
    # -------------------------
    path(
        "content/<int:grade_id>/",
        ContentAPIView.as_view(),
        name="grade-content",
    ),

    # -------------------------
    # REPORTS
    # -------------------------
    path(
        "reports/",
        ReportsAPIView.as_view(),
        name="reports",
    ),

    # -------------------------
    # DASHBOARD
    # -------------------------
    path(
        "dashboard/",
        SchoolAdminDashboardAPIView.as_view(),
        name="school-dashboard",
    ),

    # -------------------------
    # SUBSCRIPTION
    # -------------------------
    path(
        "subscription/",
        SubscriptionDeadlineAPIView.as_view(),
        name="subscription-deadline",
    ),

    # -------------------------
    # SCHOOL PROFILE
    # -------------------------
    path(
        "school/profile/",
        SchoolProfileAPIView.as_view(),
        name="school-profile",
    ),

    # -------------------------
    # REFERRAL
    # -------------------------
    path(
        "school/referral/",
        ReferralAPIView.as_view(),
        name="school-referral",
    ),

    # -------------------------
    # CONTACT
    # -------------------------
    path(
        "school/contact/",
        ContactAPIView.as_view(),
        name="school-contact",
    ),
    # -------------------------
    # STUDENT SEARCH
    # -------------------------
    path(
        "students/search/",
        StudentSearchAPIView.as_view(),
        name="student-search",
    ),

    # -------------------------
    # STUDENTS YEAR
    # -------------------------
    path(
        "students/year/",
        StudentsYearAPIView.as_view(),
        name="students-year",
    ),

    # -------------------------
    # GLOBAL SEARCH
    # -------------------------
    path(
        "search/",
        GlobalSearchAPIView.as_view(),
        name="global-search",
    ),
]