from rest_framework import serializers
from .models import SchoolRegistration, Grade


class SchoolRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolRegistration
        fields = [
            "id",
            "school_name",
            "contact_person",
            "email",
            "phone",
            "message",
            "status",
            "token",
            "created_at",
            "processed_at",
        ]
        read_only_fields = ["status", "token", "created_at", "processed_at"]


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "name", "order", "school"]
