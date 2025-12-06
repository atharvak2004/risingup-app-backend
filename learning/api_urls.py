from django.urls import path
from .views import (
    ServiceListView,
    TheoryTopicListView,
    TheoryTopicDetailView,
    CaseStudyListView,
    CaseStudyDetailView,
    SubmitCaseStudyAnswersView,
)

urlpatterns = [
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("theory/", TheoryTopicListView.as_view(), name="theory-topic-list"),
    path("theory/<int:id>/", TheoryTopicDetailView.as_view(), name="theory-topic-detail"),

    path("case-studies/", CaseStudyListView.as_view(), name="case-study-list"),
    path("case-studies/<int:id>/", CaseStudyDetailView.as_view(), name="case-study-detail"),
    path("case-studies/<int:case_study_id>/submit/", SubmitCaseStudyAnswersView.as_view(), name="case-study-submit"),
]
