from os import access

from rest_framework import serializers
from core.models import School, SchoolRegistration
from django.contrib.auth import get_user_model
from learning.models import Service
from learning.models import TheoryTopic
from learning.models import CaseStudy
from core.models import School
from core.models import Grade
from learning.models import Question, CaseStudy, CaseStudyAccess
from learning.models import AnswerOption, Question
from rest_framework import serializers
from core.models import SchoolRegistration

User = get_user_model()
class SchoolAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        
        
class SchoolListSerializer(serializers.ModelSerializer):
    admin = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "code",
            "email",
            "phone",
            "admin",
            "is_active",
            "created_at",
        ]

    def get_admin(self, obj):
        admin = User.objects.filter(
            school=obj,
            role=User.Role.SCHOOL_ADMIN
        ).first()

        if admin:
            return SchoolAdminSerializer(admin).data

        return None


class SchoolRegistrationListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolRegistration
        fields = [
            "id",
            "school_name",
            "school_email",
            "school_contact",
            "school_address",
            "school_affiliation",
            "school_trust",
            "school_principal_name",
            "school_principal_contact",
            "school_principal_email",
            "status",
            "created_at",
        ]

class AdminUserListSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(
        source="school.name", read_only=True
    )

    # 🔥 STUDENT FIELDS
    admission_no = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    section = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "school_name",

            # NEW FIELDS
            "admission_no",
            "grade",
            "section",

            "is_active",
            "is_first_login",
            "date_joined",
        ]

    def get_admission_no(self, obj):
        if obj.role == User.Role.STUDENT and hasattr(obj, "student_profile"):
            return obj.student_profile.admission_no
        return None

    def get_grade(self, obj):
        if obj.role == User.Role.STUDENT and hasattr(obj, "student_profile"):
            grade = obj.student_profile.grade
            return grade.name if grade else None
        return None

    def get_section(self, obj):
        if obj.role == User.Role.STUDENT and hasattr(obj, "student_profile"):
            section = obj.student_profile.section
            return section.name if section else None
        return None
    
    
class AdminServiceSerializer(serializers.ModelSerializer):
    school = SchoolListSerializer(read_only=True)
    school_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "school",
            "school_id",
        ]
    def create(self, validated_data):
        school_id = validated_data.pop("school_id")
        school = School.objects.get(id=school_id)
        return Service.objects.create(school=school, **validated_data)

class AdminTheoryTopicSerializer(serializers.ModelSerializer):
    service_detail = AdminServiceSerializer(source="service", read_only=True)

    class Meta:
        model = TheoryTopic
        fields = [
            "id",
            "title",
            "service",
            "service_detail",
            "grade",
            "parent",
            "order",
        ]

    def create(self, validated_data):
        service = validated_data["service"]
        grade = validated_data["grade"]

        # 🔒 Safety check: grade must belong to same school as service
        if grade.school_id != service.school_id:
            raise serializers.ValidationError(
                "Grade does not belong to the same school as service"
            )

        return TheoryTopic.objects.create(
            school=service.school,
            **validated_data
        )


class AdminCaseStudySerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()

    service_name = serializers.CharField(source="service.name", read_only=True)
    school_id = serializers.IntegerField(source="school.id", read_only=True)  # ✅ FIX

    class Meta:
        model = CaseStudy
        fields = [
            "id",
            "title",
            "description",
            "service",
            "service_name",
            "grade",
            "order",
            "is_active",
            "is_locked",
            "school_id",   
        ]

    def get_is_locked(self, obj):
        request = self.context.get("request")
        school_id = request.query_params.get("school_id")

        if not school_id:
            return False

        access = CaseStudyAccess.objects.filter(
            school_id=school_id,
            case_study=obj
        ).first()

        return access.is_locked if access else False
    def create(self, validated_data):
        service = validated_data["service"]
        grade = validated_data["grade"]

        # 🔒 SAFETY CHECK
        if service.school_id != grade.school_id:
            raise serializers.ValidationError(
                "Service and Grade must belong to the same school"
            )

        return CaseStudy.objects.create(
            school=service.school,
            **validated_data
        )
class AdminQuestionSerializer(serializers.ModelSerializer):
    case_study_detail = AdminCaseStudySerializer(source="case_study", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "case_study",
            "case_study_detail",
            "text",
            "order",
            "created_at",
        ]
        
class AdminAnswerOptionSerializer(serializers.ModelSerializer):
    question_detail = AdminQuestionSerializer(source="question", read_only=True)

    class Meta:
        model = AnswerOption
        fields = [
            "id",
            "question",
            "question_detail",
            "text",
            "is_correct",
            "created_at",
        ]

    def create(self, validated_data):
        question = validated_data["question"]

        # ensure only one correct option
        if validated_data.get("is_correct"):
            AnswerOption.objects.filter(
                question=question,
                is_correct=True
            ).update(is_correct=False)

        return super().create(validated_data)