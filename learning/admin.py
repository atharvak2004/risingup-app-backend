from django.contrib import admin
from .models import (
    Service, TheoryTopic, CaseStudy,
    Question, AnswerOption,
    StudentCaseStudyAttempt, StudentAnswer
)

# ---------------------------
# THEORY SUBTOPICS INLINE
# ---------------------------
class SubTopicInline(admin.TabularInline):
    model = TheoryTopic
    fk_name = "parent"
    extra = 1
    fields = ("title", "order")
    ordering = ("order",)


@admin.register(TheoryTopic)
class TheoryTopicAdmin(admin.ModelAdmin):
    list_display = ("title", "grade", "service", "parent", "order")
    list_filter = ("grade", "service")
    search_fields = ("title",)
    ordering = ("grade", "service", "order")
    inlines = [SubTopicInline]


# ---------------------------
# CASE STUDIES
# ---------------------------
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2
    fields = ("text", "is_correct")
    ordering = ("id",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True
    fields = ("text", "order")
    ordering = ("order",)


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ("title", "grade", "service")
    list_filter = ("grade", "service")
    search_fields = ("title", "description")
    inlines = [QuestionInline]
    ordering = ("grade", "service", "id")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "case_study", "order")
    list_filter = ("case_study",)
    inlines = [AnswerOptionInline]
    search_fields = ("text",)
    ordering = ("case_study", "order")


# ---------------------------
# STUDENT ATTEMPTS
# ---------------------------
@admin.register(StudentCaseStudyAttempt)
class StudentCaseStudyAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "case_study",
        "score",
        "correct_answers",
        "total_questions",
    )
    list_filter = ("case_study", "student")
    search_fields = ("student__username", "case_study__title")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_option", "is_correct")
    list_filter = ("attempt__student", "attempt__case_study")
    search_fields = ("question__text",)


# ---------------------------
# SERVICES
# ---------------------------
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "school")
    list_filter = ("school",)
    search_fields = ("name",)
