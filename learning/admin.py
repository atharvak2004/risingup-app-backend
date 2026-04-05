from django.contrib import admin
from .models import (
    Service, TheoryTopic, CaseStudy,
    Question, AnswerOption,
    StudentCaseStudyAttempt, StudentAnswer,
    CaseStudyAccess   # 🔥 NEW IMPORT
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
# 🔥 CASE STUDY ACCESS (LOCK/UNLOCK)
# ---------------------------
@admin.register(CaseStudyAccess)
class CaseStudyAccessAdmin(admin.ModelAdmin):
    list_display = ("school", "case_study", "is_locked", "created_at")
    list_filter = ("school", "is_locked")
    search_fields = ("school__name", "case_study__title")
    list_editable = ("is_locked",)   # 🔥 toggle directly


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
    list_display = ("title", "grade", "service", "school", "order", "is_active")
    list_filter = ("grade", "service", "school", "is_active")
    search_fields = ("title", "description")
    inlines = [QuestionInline]

    ordering = ("order",)               # 🔥 sort by order
    list_editable = ("order",)          # 🔥 inline editing

# ---------------------------
# QUESTIONS
# ---------------------------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "case_study", "order")
    list_filter = ("case_study",)
    inlines = [AnswerOptionInline]
    search_fields = ("text",)
    ordering = ("case_study", "order")


# ---------------------------
# STUDENT ATTEMPTS (ANALYTICS)
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
    list_display = ("name", "school", "is_active")
    list_filter = ("school", "is_active")
    search_fields = ("name",)