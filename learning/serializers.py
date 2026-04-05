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


# -------------------------
# BASIC SERIALIZERS
# -------------------------

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "code", "description", "icon", "is_active"]


class TheoryTopicSerializer(serializers.ModelSerializer):
    """
    Recursive serializer with nested subtopics.
    """
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
    best_score = serializers.FloatField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = CaseStudy
        fields = [
            "id",
            "title",
            "description",
            "image",
            "order",          # 🔥 ADD THIS
            "is_active",
            "best_score",
            "is_locked",
        ]


class CaseStudyDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = CaseStudy
        fields = [
            "id",
            "title",
            "description",
            "image",
            "order",       # 🔥 ADD THIS
            "is_active",
            "questions",
        ]


# -------------------------
# INPUT SERIALIZER
# -------------------------

class StudentAnswerInputSerializer(serializers.Serializer):
    """
    Used when student submits answers.
    """
    question_id = serializers.IntegerField()
    selected_option_id = serializers.IntegerField()


# -------------------------
# 🔥 NEW: DETAILED ANSWER SERIALIZER
# -------------------------

class StudentAnswerDetailSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    selected_answer = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()

    def get_selected_answer(self, obj):
        return obj.selected_option.text if obj.selected_option else None

    def get_correct_answer(self, obj):
        correct_option = obj.question.options.filter(is_correct=True).first()
        return correct_option.text if correct_option else None

    class Meta:
        model = StudentAnswer
        fields = [
            "question",
            "question_text",
            "selected_answer",
            "correct_answer",
            "is_correct",
        ]


# -------------------------
# 🔥 UPDATED ATTEMPT SERIALIZER
# -------------------------

class StudentCaseStudyAttemptSerializer(serializers.ModelSerializer):
    case_study_title = serializers.CharField(source="case_study.title", read_only=True)
    answers = StudentAnswerDetailSerializer(many=True, read_only=True)

    accuracy = serializers.SerializerMethodField()
    performance = serializers.SerializerMethodField()

    def get_accuracy(self, obj):
        if obj.total_questions == 0:
            return 0
        return round((obj.correct_answers / obj.total_questions) * 100, 2)

    def get_performance(self, obj):
        if obj.score >= 80:
            return "Excellent"
        elif obj.score >= 50:
            return "Average"
        return "Needs Improvement"

    class Meta:
        model = StudentCaseStudyAttempt
        fields = [
            "id",
            "case_study",
            "case_study_title",
            "started_at",
            "completed_at",
            "total_questions",
            "correct_answers",
            "score",
            "accuracy",
            "performance",   
            "answers",      
        ]