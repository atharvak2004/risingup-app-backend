from django.contrib import admin
from .models import SchoolReferral, ContactMessage


@admin.register(SchoolReferral)
class SchoolReferralAdmin(admin.ModelAdmin):
    list_display = ("referred_school_name", "school", "contact_person", "created_at")
    search_fields = ("referred_school_name", "contact_person", "phone", "email")
    list_filter = ("school", "created_at")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("school", "subject", "created_at")
    search_fields = ("subject", "message")
    list_filter = ("school", "created_at")
