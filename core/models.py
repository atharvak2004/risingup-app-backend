from django.db import models
import uuid
from django.utils import timezone


class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)  # internal school ID
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Grade(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="grades")
    name = models.CharField(max_length=50)  # Example: "1st Standard"
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("school", "name")
        ordering = ["order"]

    def __str__(self):
        return f"{self.school.name} - Grade {self.name}"


class Section(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="sections")
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=10)  # "A", "B", "C"

    class Meta:
        unique_together = ("grade", "name")

    def __str__(self):
        return f"{self.grade.name} - Section {self.name}"


class SchoolRegistration(models.Model):
    """
    Used by your REGISTRATION WEBSITE.
    School submits this form → superadmin approves → actual School created.
    """
    STATUS = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    school_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")

    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def approve(self):
        self.status = "APPROVED"
        self.processed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.school_name} - {self.status}"
