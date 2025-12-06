from django.db import models
from django.conf import settings


# ------------------------------
# SERVICE MODEL
# ------------------------------
class Service(models.Model):
    """
    Example services: Life Skills, Coding, STEM, Financial Literacy
    """
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="services"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)  # internal ID / slug
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="service_icons/", null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("school", "code")

    def __str__(self):
        return f"{self.school.name} - {self.name}"


# ------------------------------
# THEORY (TOPICS + SUBTOPICS)
# ------------------------------
class TheoryTopic(models.Model):
    """
    Nested theory structure:
    TOPIC → SUBTOPIC
    """
    school = models.ForeignKey("core.School", on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="theory_topics")
    grade = models.ForeignKey("core.Grade", on_delete=models.CASCADE, related_name="theory_topics")

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtopics"
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="theory_images/", null=True, blank=True)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


# ------------------------------
# CASE STUDY
# ------------------------------
class CaseStudy(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="case_studies")
    grade = models.ForeignKey("core.Grade", on_delete=models.CASCADE, related_name="case_studies")

    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="case_study_images/", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_case_studies",
    )

    def __str__(self):
        return f"{self.title} ({self.grade.name})"


# ------------------------------
# QUESTIONS
# ------------------------------
class Question(models.Model):
    case_study = models.ForeignKey(
        CaseStudy,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:40]}"


# ------------------------------
# ANSWER OPTIONS (MCQ)
# ------------------------------
class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Option: {self.text[:40]}"


# ------------------------------
# STUDENT ATTEMPTS + RESULTS
# ------------------------------
class StudentCaseStudyAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="case_study_attempts",
        limit_choices_to={"role": "STUDENT"},
    )
    case_study = models.ForeignKey(
        CaseStudy,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0)   # percentage

    def __str__(self):
        return f"{self.student.username} → {self.case_study.title} ({self.score}%)"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(
        StudentCaseStudyAttempt,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(
        AnswerOption, on_delete=models.SET_NULL, null=True
    )
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attempt.student.username} - {self.question.id}"
