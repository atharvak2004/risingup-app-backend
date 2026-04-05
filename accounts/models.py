from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Admin"
        SCHOOL_ADMIN = "SCHOOL_ADMIN", "School Admin"
        STAFF = "STAFF", "Staff"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    # NEW FIELD — first login flag
    is_first_login = models.BooleanField(default=True)

    # School link
    school = models.ForeignKey(
        "core.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    grade = models.ForeignKey(
        "core.Grade", on_delete=models.SET_NULL, null=True, blank=True
    )
    section = models.ForeignKey(
        "core.Section", on_delete=models.SET_NULL, null=True, blank=True
    )
    admission_no = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Student: {self.user.username}"


class StaffProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="staff_profile"
    )
    designation = models.CharField(max_length=100, blank=True)
    is_class_teacher = models.BooleanField(default=False)

    assigned_grade = models.ForeignKey(
        "core.Grade", on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_section = models.ForeignKey(
        "core.Section", on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Staff: {self.user.username}"
