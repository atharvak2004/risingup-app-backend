from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import BooleanField, Max, Q, Value
from .models import (
    Service,
    TheoryTopic,
    CaseStudy,
    Question,
    AnswerOption,
    StudentCaseStudyAttempt,
    StudentAnswer,
    CaseStudyAccess,
)
from .serializers import (
    ServiceSerializer,
    TheoryTopicSerializer,
    CaseStudyListSerializer,
    CaseStudyDetailSerializer,
    StudentAnswerInputSerializer,
    StudentCaseStudyAttemptSerializer,
)
from accounts.permissions import IsStudent
from django.db.models.functions import Coalesce

# -------------------------
# SERVICES LIST (for school)
# -------------------------
class ServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")

        if not school_id and self.request.user.school_id:
            school_id = self.request.user.school_id

        qs = Service.objects.filter(is_active=True)

        if not school_id:
            return qs.none()

        return qs.filter(school_id=school_id)


# -------------------------
# THEORY TOPICS BY GRADE + SERVICE
# -------------------------
class TheoryTopicListView(generics.ListAPIView):
    serializer_class = TheoryTopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        service_id = self.request.query_params.get("service_id")
        grade_id = self.request.query_params.get("grade_id")

        qs = TheoryTopic.objects.filter(parent__isnull=True)

        # Scope to user's school by default
        user_school = self.request.user.school
        if user_school:
            qs = qs.filter(school=user_school)

        if service_id:
            qs = qs.filter(service_id=service_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)

        # Optimize nested subtopics loading
        return qs.select_related("service", "grade").prefetch_related("subtopics")


class TheoryTopicDetailView(generics.RetrieveAPIView):
    queryset = TheoryTopic.objects.all()
    serializer_class = TheoryTopicSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        qs = super().get_queryset()
        user_school = self.request.user.school
        if user_school:
            qs = qs.filter(school=user_school)
        return qs


# -------------------------
# CASE STUDY LIST (grade + service)
# -------------------------
from django.db.models import Max, Q, OuterRef, Subquery

class CaseStudyListView(generics.ListAPIView):
    """
    List case studies for a grade + service.
    """
    serializer_class = CaseStudyListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["created_at", "title", "order"]

    def get_queryset(self):
        service_id = self.request.query_params.get("service_id")
        grade_id = self.request.query_params.get("grade_id")
        user = self.request.user

        qs = CaseStudy.objects.filter(is_active=True)

        if user.school:
            qs = qs.filter(school=user.school)

        if service_id:
            qs = qs.filter(service_id=service_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)

        # 🔥 BEST SCORE
        qs = qs.annotate(
            best_score=Max(
                "attempts__score",
                filter=Q(attempts__student=user)
            )
        )

        # 🔥 LOCK STATUS (IMPORTANT)
        access_subquery = CaseStudyAccess.objects.filter(
            school_id=user.school_id,   # ✅ FIXED
            case_study_id=OuterRef("pk")  # ✅ FIXED
        ).values("is_locked")[:1]

        print("USER:", user)
        print("USER SCHOOL:", user.school)
        print("USER SCHOOL ID:", user.school_id)

        qs = qs.annotate(
            is_locked=Coalesce(
                Subquery(access_subquery),
                Value(False),
                output_field=BooleanField()
            )
        )

        print("---- DEBUG CASE STUDIES ----")
        for c in qs:
            print(f"Case {c.id} → is_locked: {c.is_locked}")
        print("----------------------------")

        return qs.order_by("order").select_related("grade", "service")
    
# -------------------------
# CASE STUDY DETAIL (with questions + options)
# -------------------------
class CaseStudyDetailView(generics.RetrieveAPIView):
    """
    Get full case study with all questions and options.
    /api/learning/case-studies/<id>/
    """
    serializer_class = CaseStudyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        qs = CaseStudy.objects.all()

        if user.school:
            qs = qs.filter(school=user.school)

        return qs.prefetch_related("questions__options")


    def get(self, request, *args, **kwargs):
        case_study = self.get_object()

        access = CaseStudyAccess.objects.filter(
            school=request.user.school,
            case_study=case_study
        ).first()

        if access and access.is_locked:
            return Response(
                {"detail": "This case study is locked."},
                status=403
            )

        return super().get(request, *args, **kwargs)


class SubmitCaseStudyAnswersView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request, case_study_id):
        # Scope case study to user's school
        user = request.user
        case_study = (
            CaseStudy.objects.filter(id=case_study_id, is_active=True)
            .select_related("school")
            .first()
        )

        if not case_study:
            return Response({"detail": "Case study not found."}, status=404)

        if user.school and case_study.school != user.school:
            return Response(
                {"detail": "You cannot attempt a case study from another school."},
                status=403,
            )

        serializer = StudentAnswerInputSerializer(
            data=request.data.get("answers", []),
            many=True,
        )
        serializer.is_valid(raise_exception=True)
        answers_data = serializer.validated_data

        # Prefetch questions & options for performance
        questions = (
            Question.objects.filter(case_study=case_study)
            .prefetch_related("options")
        )
        question_map = {q.id: q for q in questions}
        option_map = {}
        for q in questions:
            for opt in q.options.all():
                option_map[opt.id] = opt

        # Create attempt
        attempt = StudentCaseStudyAttempt.objects.create(
            student=user,
            case_study=case_study,
        )

        total_questions = 0
        correct_answers = 0

        for ans in answers_data:
            qid = ans["question_id"]
            oid = ans["selected_option_id"]

            question = question_map.get(qid)
            if not question:
                # ignore invalid question ids
                continue

            option = option_map.get(oid)
            is_correct = option.is_correct if option else False

            StudentAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=option,
                is_correct=is_correct,
            )

            total_questions += 1
            if is_correct:
                correct_answers += 1

        # compute score
        attempt.total_questions = total_questions
        attempt.correct_answers = correct_answers
        attempt.score = (
            (correct_answers / total_questions * 100) if total_questions > 0 else 0
        )
        attempt.save()

        output_serializer = StudentCaseStudyAttemptSerializer(attempt)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
