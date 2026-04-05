from django.db import models
from core.models import School


class SchoolReferral(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="referrals")
    referred_school_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Referral by {self.school.name} → {self.referred_school_name}"


class ContactMessage(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="contact_messages")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} - {self.subject}"
