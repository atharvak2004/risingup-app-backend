from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Service,
    TheoryTopic,
    CaseStudy,
    Question,
    AnswerOption,
    StudentCaseStudyAttempt,
    StudentAnswer,
)
from core.models import Grade, School
from .serializers import (
    ServiceSerializer,
    TheoryTopicSerializer,
    CaseStudyListSerializer,
    CaseStudyDetailSerializer,
    StudentAnswerInputSerializer,
    StudentCaseStudyAttemptSerializer,
)


# -------------------------
# SERVICES LIST (for school)
# -------------------------
class ServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.query_params.get("school_id")
        qs = Service.objects.filter(is_active=True)

        # Require school_id – if not provided, return no results
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

        if service_id:
            qs = qs.filter(service_id=service_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)

        # Optimize nested subtopics loading
        return qs.select_related("service", "grade").prefetch_related("subtopics").order_by("order")

class TheoryTopicDetailView(generics.RetrieveAPIView):
    queryset = TheoryTopic.objects.all()
    serializer_class = TheoryTopicSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

# -------------------------
# CASE STUDY LIST (grade + service)
# -------------------------
class CaseStudyListView(generics.ListAPIView):
    """
    List case studies for a grade + service.
    /api/learning/case-studies/?service_id=1&grade_id=2
    """
    serializer_class = CaseStudyListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        service_id = self.request.query_params.get("service_id")
        grade_id = self.request.query_params.get("grade_id")

        qs = CaseStudy.objects.filter(is_active=True)
        if service_id:
            qs = qs.filter(service_id=service_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)
        return qs


# -------------------------
# CASE STUDY DETAIL (with questions + options)
# -------------------------
class CaseStudyDetailView(generics.RetrieveAPIView):
    """
    Get full case study with all questions and options.
    /api/learning/case-studies/<id>/
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


class SubmitCaseStudyAnswersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, case_study_id):
        case_study = CaseStudy.objects.filter(id=case_study_id, is_active=True).first()
        if not case_study:
            return Response({"detail": "Case study not found."}, status=404)

        user = request.user
        if getattr(user, "role", None) != "STUDENT":
            return Response({"detail": "Only students can submit attempts."}, status=403)

        serializer = StudentAnswerInputSerializer(data=request.data.get("answers", []), many=True)
        serializer.is_valid(raise_exception=True)

        answers_data = serializer.validated_data

        # create attempt
        attempt = StudentCaseStudyAttempt.objects.create(
            student=user,
            case_study=case_study,
        )

        total_questions = 0
        correct_answers = 0

        for ans in answers_data:
            qid = ans["question_id"]
            oid = ans["selected_option_id"]

            try:
                question = Question.objects.get(id=qid, case_study=case_study)
            except Question.DoesNotExist:
                # ignore invalid question ids
                continue

            try:
                option = AnswerOption.objects.get(id=oid, question=question)
            except AnswerOption.DoesNotExist:
                option = None

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
        attempt.score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        attempt.save()

        output_serializer = StudentCaseStudyAttemptSerializer(attempt)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
