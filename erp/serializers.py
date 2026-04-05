from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import StudentProfile
from core.models import School, Grade, Section
from learning.models import TheoryTopic, CaseStudy, StudentCaseStudyAttempt
from .models import SchoolReferral, ContactMessage

User = get_user_model()


# -----------------------------
# BASIC SERIALIZERS
# -----------------------------
class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "name"]


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name"]


# -----------------------------
# STUDENT PROFILE
# -----------------------------
class StudentProfileSerializer(serializers.ModelSerializer):

    grade = GradeSerializer(read_only=True)
    section = SectionSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "admission_no",
            "grade",
            "section",
        ]


# -----------------------------
# FULL STUDENT SERIALIZER
# -----------------------------
class StudentSerializer(serializers.ModelSerializer):

    student_profile = StudentProfileSerializer(read_only=True)

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "student_profile",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


# -----------------------------
# ADD STUDENT
# -----------------------------
class AddStudentSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=6)

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    grade_id = serializers.IntegerField()
    section_id = serializers.IntegerField()
    admission_no = serializers.CharField(max_length=50)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate(self, data):

        grade_id = data.get("grade_id")
        section_id = data.get("section_id")

        if not Grade.objects.filter(id=grade_id).exists():
            raise serializers.ValidationError({"grade_id": "Invalid grade"})

        if not Section.objects.filter(id=section_id).exists():
            raise serializers.ValidationError({"section_id": "Invalid section"})

        return data


# -----------------------------
# STUDENT LIST (FAST LIST VIEW)
# -----------------------------
class StudentListSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    email = serializers.CharField(source="user.email")

    full_name = serializers.SerializerMethodField()

    grade = serializers.CharField(source="grade.name")
    section = serializers.CharField(source="section.name")

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "admission_no",
            "grade",
            "section",
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()


# -----------------------------
# STUDENT PROGRESS
# -----------------------------
class StudentProgressSerializer(serializers.ModelSerializer):

    case_study_id = serializers.IntegerField(source="case_study.id")
    case_study_title = serializers.CharField(source="case_study.title")

    class Meta:
        model = StudentCaseStudyAttempt
        fields = [
            "case_study_id",
            "case_study_title",
            "score",
            "completed_at",
        ]


# -----------------------------
# CONTENT SERIALIZERS
# -----------------------------
class ChapterSerializer(serializers.ModelSerializer):

    class Meta:
        model = TheoryTopic
        fields = [
            "id",
            "title",
            "description",
        ]


class TestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CaseStudy
        fields = [
            "id",
            "title",
            "description",
        ]


# -----------------------------
# REPORTS
# -----------------------------
class ReportSerializer(serializers.Serializer):

    total_students = serializers.IntegerField()
    completed_tests = serializers.IntegerField()
    pending_tests = serializers.IntegerField()

    completion_rate = serializers.FloatField()
    average_score = serializers.FloatField()


# -----------------------------
# REFERRALS
# -----------------------------
class SchoolReferralSerializer(serializers.ModelSerializer):

    class Meta:
        model = SchoolReferral
        fields = [
            "id",
            "referred_school_name",
            "contact_person",
            "phone",
            "email",
            "message",
            "created_at",
        ]


# -----------------------------
# CONTACT
# -----------------------------
class ContactMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactMessage
        fields = [
            "id",
            "subject",
            "message",
            "created_at",
        ]


# -----------------------------
# SCHOOL PROFILE UPDATE
# -----------------------------
class SchoolProfileUpdateSerializer(serializers.Serializer):

    admin_name = serializers.CharField(required=False)
    admin_email = serializers.EmailField(required=False)
    admin_phone = serializers.CharField(required=False)

    school_name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)


# -----------------------------
# SCHOOL PROFILE RESPONSE
# -----------------------------
class SchoolProfileSerializer(serializers.Serializer):

    admin = serializers.SerializerMethodField()
    school = serializers.SerializerMethodField()

    def get_admin(self, obj):

        user = obj["user"]

        return {
            "username": user.username,
            "full_name": user.get_full_name(),
            "email": user.email,
            "phone": user.phone,
        }

    def get_school(self, obj):

        school = obj["school"]

        return {
            "id": school.id,
            "school_name": school.name,
            "email": school.email,
            "phone": school.phone,
            "address": school.address,
            "city": school.city,
            "state": school.state,
            "country": school.country,
            "code": school.code,
            "is_active": school.is_active,
        }