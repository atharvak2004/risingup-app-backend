from rest_framework import serializers
from .models import (
    Service,
    TheoryTopic,
    CaseStudy,
    Question,
    AnswerOption,
    StudentCaseStudyAttempt,
    StudentAnswer,
)
from core.models import Grade
from accounts.models import User


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "code", "description", "icon", "is_active"]
        

class TheoryTopicSerializer(serializers.ModelSerializer):
    subtopics = serializers.SerializerMethodField()

    class Meta:
        model = TheoryTopic
        fields = [
            "id",
            "title",
            "description",
            "image",
            "order",
            "parent",
            "subtopics",
        ]

    def get_subtopics(self, obj):
        children = obj.subtopics.all().order_by("order")
        return TheoryTopicSerializer(children, many=True).data

class TheoryTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheoryTopic
        fields = ["id", "title", "description", "image", "parent"]

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "options"]


class CaseStudyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ["id", "title", "description", "image", "is_active"]


class CaseStudyDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = CaseStudy
        fields = [
            "id",
            "title",
            "description",
            "image",
            "is_active",
            "questions",
        ]


class StudentAnswerInputSerializer(serializers.Serializer):
    """
    Used when student submits answers.
    """
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField()


class StudentCaseStudyAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCaseStudyAttempt
        fields = [
            "id",
            "case_study",
            "started_at",
            "completed_at",
            "total_questions",
            "correct_answers",
            "score",
        ]
