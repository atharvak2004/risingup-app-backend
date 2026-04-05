from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, StaffProfile


class UserAdmin(BaseUserAdmin):
    model = User

    # Fields shown in admin list
    list_display = ("id", "username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    # Fieldsets (edit page)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("role", "school", "phone", "is_first_login")}),
    )

    # Add user form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Custom Fields", {"fields": ("role", "school", "phone")}),
    )

    search_fields = ("username", "email")
    ordering = ("id",)


admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile)
admin.site.register(StaffProfile)