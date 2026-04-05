from rest_framework import serializers
from .models import SchoolRegistration, Grade


class SchoolRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolRegistration
        fields = [
            "id",
            "school_name",
            "school_email",
            "school_contact",
            "school_address",
            "school_website",
            "school_affiliation",
            "school_trust",
            "school_gst_number",
            "school_principal_name",
            "school_principal_contact",
            "school_principal_email",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "name", "order", "school"]
